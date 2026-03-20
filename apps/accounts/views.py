from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.text import slugify

from apps.core.models import Subscription, Tenant

from .forms import (
    ForgotPasswordForm,
    LoginForm,
    RegisterForm,
    UserInviteForm,
    UserProfileForm,
)
from .models import Role, UserInvite

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        remember = form.cleaned_data.get('remember', False)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if not remember:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Create the tenant
        company_name = form.cleaned_data['company_name']
        slug = slugify(company_name)

        # Ensure slug uniqueness
        base_slug = slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        tenant = Tenant.objects.create(
            name=company_name,
            slug=slug,
        )

        # Create default subscription (free plan)
        Subscription.objects.create(
            tenant=tenant,
            plan='free',
            status='active',
            max_users=5,
            max_storage_gb=1,
            start_date=date.today(),
        )

        # Create default Admin role for the tenant
        admin_role = Role.objects.create(
            tenant=tenant,
            name='Admin',
            slug='admin',
            description='Default administrator role',
            is_system_role=True,
            permissions=[],
        )

        # Create the user
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            tenant=tenant,
            role=admin_role,
            is_tenant_admin=True,
        )

        # Auto login
        login(request, user)
        messages.success(
            request,
            'Your account has been created successfully. Welcome to NavHCM!',
        )
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')
    return redirect('accounts:login')


def forgot_password_view(request):
    form = ForgotPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        messages.success(
            request,
            'If an account with that email exists, we have sent password '
            'reset instructions to your email address.',
        )
        return redirect('accounts:login')

    return render(request, 'auth/forgot_password.html', {'form': form})


@login_required
def user_list_view(request):
    tenant = request.tenant
    users = User.objects.filter(tenant=tenant)
    roles = Role.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(username__icontains=search_query)
        )

    role_filter = request.GET.get('role', '').strip()
    if role_filter:
        users = users.filter(role_id=role_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'roles': roles,
        'search_query': search_query,
    })


@login_required
def user_invite_view(request):
    tenant = request.tenant
    form = UserInviteForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        UserInvite.objects.create(
            tenant=tenant,
            email=form.cleaned_data['email'],
            role=form.cleaned_data.get('role'),
            invited_by=request.user,
            message=form.cleaned_data.get('message', ''),
        )
        messages.success(
            request,
            f'Invitation sent to {form.cleaned_data["email"]}.',
        )
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_invite.html', {'form': form})


@login_required
def profile_view(request):
    form = UserProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile_user': request.user,
    })


@login_required
def role_list_view(request):
    tenant = request.tenant
    roles = Role.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        roles = roles.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        roles = roles.filter(is_active=True)
    elif status_filter == 'inactive':
        roles = roles.filter(is_active=False)

    type_filter = request.GET.get('type', '').strip()
    if type_filter == 'system':
        roles = roles.filter(is_system_role=True)
    elif type_filter == 'custom':
        roles = roles.filter(is_system_role=False)

    return render(request, 'accounts/role_list.html', {
        'roles': roles,
    })


@login_required
def permission_list_view(request):
    tenant = request.tenant
    if tenant:
        roles = list(Role.objects.filter(tenant=tenant, is_active=True))
    elif request.user.is_superuser:
        roles = list(Role.objects.filter(is_active=True))
    else:
        roles = []

    # Collect all unique permissions across all roles
    all_permissions = set()
    for role in roles:
        if role.permissions:
            all_permissions.update(role.permissions)
    all_permissions = sorted(all_permissions)

    # Build matrix: each row has name, codename, and a list of booleans
    # matching the order of `roles`
    permission_matrix = []
    for perm in all_permissions:
        row = {
            'name': perm.replace('_', ' ').title(),
            'codename': perm,
            'checks': [perm in (role.permissions or []) for role in roles],
        }
        permission_matrix.append(row)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        permission_matrix = [
            p for p in permission_matrix
            if search_query.lower() in p['name'].lower()
            or search_query.lower() in p['codename'].lower()
        ]

    return render(request, 'accounts/permission_list.html', {
        'roles': roles,
        'permission_matrix': permission_matrix,
    })
