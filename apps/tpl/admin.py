from django.contrib import admin

from .models import (
    BillingInvoice,
    BillingInvoiceItem,
    BillingRate,
    Client,
    ClientInventoryItem,
    ClientStorageZone,
    IntegrationConfig,
    IntegrationLog,
    RentalAgreement,
    SLA,
    SLAMetric,
    SpaceUsageRecord,
)


# =============================================================================
# Client
# =============================================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_number', 'name', 'status', 'default_currency', 'tenant', 'created_at')
    list_filter = ('status', 'default_currency', 'tenant')
    search_fields = ('client_number', 'name', 'email')


# =============================================================================
# Billing
# =============================================================================

@admin.register(BillingRate)
class BillingRateAdmin(admin.ModelAdmin):
    list_display = ('rate_number', 'client', 'rate_type', 'rate_amount', 'currency', 'is_active', 'tenant')
    list_filter = ('rate_type', 'is_active', 'tenant')
    search_fields = ('rate_number', 'description')


class BillingInvoiceItemInline(admin.TabularInline):
    model = BillingInvoiceItem
    extra = 1


@admin.register(BillingInvoice)
class BillingInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'status', 'total_amount', 'currency', 'due_date', 'tenant')
    list_filter = ('status', 'currency', 'tenant')
    search_fields = ('invoice_number',)
    inlines = [BillingInvoiceItemInline]


# =============================================================================
# Client Inventory Segregation
# =============================================================================

@admin.register(ClientStorageZone)
class ClientStorageZoneAdmin(admin.ModelAdmin):
    list_display = ('zone_number', 'zone_name', 'client', 'zone_type', 'warehouse', 'is_active', 'tenant')
    list_filter = ('zone_type', 'is_active', 'tenant')
    search_fields = ('zone_number', 'zone_name')


@admin.register(ClientInventoryItem)
class ClientInventoryItemAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'item_name', 'client', 'quantity', 'weight', 'tenant')
    list_filter = ('weight_unit', 'tenant')
    search_fields = ('tracking_number', 'item_name', 'sku')


# =============================================================================
# SLA Management
# =============================================================================

class SLAMetricInline(admin.TabularInline):
    model = SLAMetric
    extra = 1


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ('sla_number', 'title', 'client', 'status', 'effective_date', 'expiry_date', 'tenant')
    list_filter = ('status', 'review_frequency', 'tenant')
    search_fields = ('sla_number', 'title')
    inlines = [SLAMetricInline]


# =============================================================================
# Client Integration
# =============================================================================

class IntegrationLogInline(admin.TabularInline):
    model = IntegrationLog
    extra = 0
    readonly_fields = ('log_type', 'direction', 'status', 'records_processed', 'records_failed', 'started_at', 'completed_at')


@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    list_display = ('config_number', 'integration_name', 'client', 'status', 'sync_direction', 'sync_frequency', 'tenant')
    list_filter = ('status', 'sync_direction', 'sync_frequency', 'tenant')
    search_fields = ('config_number', 'integration_name')
    inlines = [IntegrationLogInline]


# =============================================================================
# Warehouse Rental
# =============================================================================

class SpaceUsageRecordInline(admin.TabularInline):
    model = SpaceUsageRecord
    extra = 1


@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):
    list_display = ('agreement_number', 'client', 'status', 'space_type', 'warehouse', 'rate_amount', 'currency', 'tenant')
    list_filter = ('status', 'space_type', 'tenant')
    search_fields = ('agreement_number',)
    inlines = [SpaceUsageRecordInline]
