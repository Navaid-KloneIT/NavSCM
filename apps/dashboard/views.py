from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.models import Role, User, UserInvite


@login_required
def dashboard_view(request):
    tenant = getattr(request, 'tenant', None)

    if tenant:
        total_users = User.objects.filter(tenant=tenant).count()
        active_users = User.objects.filter(tenant=tenant, is_active=True).count()
        pending_invites = UserInvite.objects.filter(tenant=tenant, status='pending').count()
        total_roles = Role.objects.filter(tenant=tenant).count()
        recent_users = User.objects.filter(tenant=tenant).order_by('-date_joined')[:5]
        recent_invites = UserInvite.objects.filter(tenant=tenant).order_by('-created_at')[:5]
    else:
        total_users = 0
        active_users = 0
        pending_invites = 0
        total_roles = 0
        recent_users = []
        recent_invites = []

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'pending_invites': pending_invites,
        'total_roles': total_roles,
        'recent_users': recent_users,
        'recent_invites': recent_invites,
    }

    return render(request, 'dashboard/index.html', context)
