from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from .models import AuditLog, Subscription, Tenant


@login_required
def tenant_list_view(request):
    if request.user.is_superuser:
        tenants = Tenant.objects.all()
    else:
        tenants = Tenant.objects.filter(id=request.user.tenant_id)

    return render(request, 'core/tenant_list.html', {
        'tenants': tenants,
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

    return render(request, 'core/subscription_plans.html', {
        'subscription': subscription,
    })


@login_required
def subscription_billing_view(request):
    return render(request, 'core/subscription_billing.html')


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

    return render(request, 'core/audit_logs.html', {
        'logs': logs,
        'search_query': search_query,
    })


@login_required
def security_view(request):
    return render(request, 'core/security.html')
