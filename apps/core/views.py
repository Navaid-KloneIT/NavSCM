import io
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from .models import AuditLog, Subscription, Tenant


@login_required
def tenant_list_view(request):
    if request.user.is_superuser:
        tenants = Tenant.objects.all()
    else:
        tenants = Tenant.objects.filter(id=request.user.tenant_id)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tenants = tenants.filter(
            Q(name__icontains=search_query)
            | Q(slug__icontains=search_query)
            | Q(domain__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        tenants = tenants.filter(is_active=True)
    elif status_filter == 'inactive':
        tenants = tenants.filter(is_active=False)

    return render(request, 'core/tenant_list.html', {
        'tenants': tenants,
    })


@login_required
def tenant_detail_view(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)

    if not request.user.is_superuser and request.user.tenant_id != tenant.pk:
        return redirect('core:tenant_list')

    subscription = None
    try:
        subscription = tenant.subscription
    except Subscription.DoesNotExist:
        pass

    user_count = tenant.users.count()
    role_count = tenant.roles.count()
    recent_logs = tenant.audit_logs.select_related('user')[:10]

    return render(request, 'core/tenant_detail.html', {
        'tenant': tenant,
        'subscription': subscription,
        'user_count': user_count,
        'role_count': role_count,
        'recent_logs': recent_logs,
    })


@login_required
def tenant_add_view(request):
    if request.method == 'POST':
        # TODO: Handle tenant creation form submission
        pass

    return render(request, 'core/tenant_add.html')


@login_required
def subscription_plans_view(request):
    subscription = None
    if request.user.tenant:
        try:
            subscription = request.user.tenant.subscription
        except Subscription.DoesNotExist:
            pass
    elif request.user.is_superuser:
        subscription = Subscription.objects.select_related('tenant').first()

    return render(request, 'core/subscription_plans.html', {
        'subscription': subscription,
    })


def _get_billing_subscription(user):
    """Get subscription for billing views - handles both tenant users and superusers."""
    if user.tenant:
        try:
            return user.tenant.subscription
        except Subscription.DoesNotExist:
            return None
    elif user.is_superuser:
        return Subscription.objects.select_related('tenant').first()
    return None


def _build_invoices(subscription):
    """Build sample invoice list from subscription data."""
    if not subscription:
        return []
    price_map = {'free': 0, 'starter': 29, 'professional': 79, 'enterprise': 199}
    amount = price_map.get(subscription.plan, 0)
    start = subscription.start_date
    invoices = []
    for i in range(6):
        invoices.append({
            'number': f'INV-{start.year}{start.month:02d}-{1000 + i}',
            'date': start - timedelta(days=30 * i),
            'amount': amount,
            'status': 'paid' if i > 0 else 'current',
            'plan': subscription.get_plan_display(),
        })
    return invoices


# Sample payment method stored in session for demo purposes
DEFAULT_PAYMENT_METHOD = {
    'card_brand': 'Visa',
    'card_last4': '4242',
    'card_expiry': '12/2027',
    'card_holder': '',
}


def _get_payment_method(request):
    """Get payment method from session or return default sample data."""
    return request.session.get('payment_method', DEFAULT_PAYMENT_METHOD)


@login_required
def subscription_billing_view(request):
    subscription = _get_billing_subscription(request.user)

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').replace(' ', '')
        card_expiry = request.POST.get('card_expiry', '').strip()
        card_holder = request.POST.get('card_holder', '').strip()

        errors = []
        if not card_number or len(card_number) < 13 or not card_number.isdigit():
            errors.append('Please enter a valid card number.')
        if not card_expiry or '/' not in card_expiry:
            errors.append('Please enter a valid expiry date (MM/YY).')
        if not card_holder:
            errors.append('Please enter the cardholder name.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Determine card brand from first digit
            brand_map = {'4': 'Visa', '5': 'Mastercard', '3': 'Amex', '6': 'Discover'}
            card_brand = brand_map.get(card_number[0], 'Card')

            request.session['payment_method'] = {
                'card_brand': card_brand,
                'card_last4': card_number[-4:],
                'card_expiry': card_expiry,
                'card_holder': card_holder,
            }
            messages.success(request, 'Payment method updated successfully.')

        return redirect('core:subscription_billing')

    invoices = _build_invoices(subscription)
    payment_method = _get_payment_method(request)

    return render(request, 'core/subscription_billing.html', {
        'subscription': subscription,
        'invoices': invoices,
        'payment_method': payment_method,
    })


@login_required
def invoice_download_view(request, invoice_number):
    subscription = _get_billing_subscription(request.user)
    if not subscription:
        messages.error(request, 'No subscription found.')
        return redirect('core:subscription_billing')

    invoices = _build_invoices(subscription)
    invoice = None
    for inv in invoices:
        if inv['number'] == invoice_number:
            invoice = inv
            break

    if not invoice:
        messages.error(request, 'Invoice not found.')
        return redirect('core:subscription_billing')

    tenant_name = subscription.tenant.name
    tenant_domain = subscription.tenant.domain or 'company.com'

    # Render HTML template to string
    html_string = render_to_string('core/invoice_pdf.html', {
        'invoice': {
            'number': invoice['number'],
            'date': invoice['date'].strftime('%B %d, %Y'),
            'amount': invoice['amount'],
            'status': invoice['status'],
            'status_display': invoice['status'].upper(),
            'plan': invoice['plan'],
        },
        'tenant_name': tenant_name,
        'tenant_domain': tenant_domain,
        'billing_email': f'billing@{tenant_domain}',
    })

    # Generate PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)

    if pisa_status.err:
        messages.error(request, 'Failed to generate PDF.')
        return redirect('core:subscription_billing')

    pdf_buffer.seek(0)
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice["number"]}.pdf"'
    return response


@login_required
def audit_log_view(request):
    if request.user.is_superuser:
        logs = AuditLog.objects.all()
    else:
        logs = AuditLog.objects.filter(tenant=request.user.tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        logs = logs.filter(
            Q(action__icontains=search_query)
            | Q(model_name__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    action_filter = request.GET.get('action', '').strip()
    if action_filter:
        logs = logs.filter(action=action_filter)

    return render(request, 'core/audit_logs.html', {
        'logs': logs,
        'search_query': search_query,
    })


@login_required
def security_view(request):
    return render(request, 'core/security.html')
