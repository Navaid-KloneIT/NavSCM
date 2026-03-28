from django.contrib import admin

from .models import (
    Disposition,
    Refund,
    ReturnAuthorization,
    ReturnPortalSettings,
    RMALineItem,
    WarrantyClaim,
    WarrantyClaimItem,
)


# Inlines
class RMALineItemInline(admin.TabularInline):
    model = RMALineItem
    extra = 1


class WarrantyClaimItemInline(admin.TabularInline):
    model = WarrantyClaimItem
    extra = 1


# Main Admins
@admin.register(ReturnAuthorization)
class ReturnAuthorizationAdmin(admin.ModelAdmin):
    list_display = (
        'rma_number', 'customer', 'return_type', 'reason_category',
        'status', 'priority', 'requested_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'return_type', 'reason_category', 'priority', 'tenant')
    search_fields = ('rma_number', 'customer__name')
    inlines = [RMALineItemInline]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        'refund_number', 'rma', 'refund_type', 'refund_method',
        'amount', 'currency', 'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'refund_type', 'refund_method', 'tenant')
    search_fields = ('refund_number', 'rma__rma_number')


@admin.register(Disposition)
class DispositionAdmin(admin.ModelAdmin):
    list_display = (
        'disposition_number', 'rma', 'item', 'condition_received',
        'disposition_decision', 'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'condition_received', 'disposition_decision', 'tenant')
    search_fields = ('disposition_number', 'item__name')


@admin.register(WarrantyClaim)
class WarrantyClaimAdmin(admin.ModelAdmin):
    list_display = (
        'claim_number', 'vendor', 'item', 'claim_type', 'status',
        'claim_amount', 'currency', 'tenant', 'created_at',
    )
    list_filter = ('status', 'claim_type', 'tenant')
    search_fields = ('claim_number', 'vendor__name', 'item__name')
    inlines = [WarrantyClaimItemInline]


@admin.register(ReturnPortalSettings)
class ReturnPortalSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'tenant', 'is_portal_enabled', 'return_window_days',
        'requires_approval', 'restocking_fee_percentage',
    )
    list_filter = ('is_portal_enabled', 'requires_approval')
