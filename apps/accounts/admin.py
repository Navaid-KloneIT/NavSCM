from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Role, User, UserInvite


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'tenant', 'is_system_role', 'is_active', 'created_at')
    list_filter = ('is_system_role', 'is_active', 'tenant')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'tenant',
        'role', 'is_tenant_admin', 'is_active',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_tenant_admin', 'tenant', 'role')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tenant & Role', {
            'fields': ('tenant', 'role', 'is_tenant_admin'),
        }),
        ('Profile', {
            'fields': ('phone', 'avatar', 'job_title', 'department', 'bio'),
        }),
        ('Tracking', {
            'fields': ('last_login_ip',),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Tenant & Role', {
            'fields': ('tenant', 'role', 'is_tenant_admin'),
        }),
    )


@admin.register(UserInvite)
class UserInviteAdmin(admin.ModelAdmin):
    list_display = ('email', 'tenant', 'role', 'status', 'invited_by', 'created_at', 'expires_at')
    list_filter = ('status', 'tenant')
    search_fields = ('email', 'token')
    readonly_fields = ('id', 'token', 'created_at', 'accepted_at')
