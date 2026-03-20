from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

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


@login_required
def subscription_billing_view(request):
    subscription = None
    if request.user.tenant:
        try:
            subscription = request.user.tenant.subscription
        except Subscription.DoesNotExist:
            pass
    elif request.user.is_superuser:
        subscription = Subscription.objects.select_related('tenant').first()

    # Build sample billing history from subscription data
    invoices = []
    if subscription:
        from datetime import timedelta
        price_map = {'free': 0, 'starter': 29, 'professional': 79, 'enterprise': 199}
        amount = price_map.get(subscription.plan, 0)
        start = subscription.start_date
        for i in range(6):
            invoices.append({
                'number': f'INV-{start.year}{start.month:02d}-{1000 + i}',
                'date': start - timedelta(days=30 * i),
                'amount': f'${amount}.00',
                'status': 'paid' if i > 0 else 'current',
                'plan': subscription.get_plan_display(),
            })

    return render(request, 'core/subscription_billing.html', {
        'subscription': subscription,
        'invoices': invoices,
    })


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
