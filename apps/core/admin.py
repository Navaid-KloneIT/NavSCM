from django.contrib import admin

from .models import AuditLog, Subscription, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'domain', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'domain')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'plan', 'status', 'max_users', 'start_date', 'end_date')
    list_filter = ('plan', 'status')
    search_fields = ('tenant__name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'model_name', 'user', 'tenant', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('action', 'model_name', 'object_id', 'user__email')
    readonly_fields = ('id', 'timestamp', 'changes')
