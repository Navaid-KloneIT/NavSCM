from django.contrib import admin

from .models import (
    CatalogItem,
    OrderTracking,
    PortalAccount,
    PortalDocument,
    SupportTicket,
    TicketMessage,
    TrackingEvent,
)


# Inlines
class TrackingEventInline(admin.TabularInline):
    model = TrackingEvent
    extra = 1


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1


# Main Admins
@admin.register(PortalAccount)
class PortalAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_number', 'display_name', 'customer', 'status',
        'payment_method', 'tenant', 'created_at',
    )
    list_filter = ('status', 'payment_method', 'tenant')
    search_fields = ('account_number', 'display_name', 'portal_email')


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_number', 'portal_account', 'order', 'current_status',
        'carrier_name', 'estimated_delivery', 'tenant', 'created_at',
    )
    list_filter = ('current_status', 'tenant')
    search_fields = ('tracking_number', 'carrier_name', 'order__order_number')
    inlines = [TrackingEventInline]


@admin.register(PortalDocument)
class PortalDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_number', 'portal_account', 'document_type', 'title',
        'status', 'issue_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'document_type', 'tenant')
    search_fields = ('document_number', 'title', 'reference_number')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number', 'portal_account', 'subject', 'category',
        'priority', 'status', 'assigned_to', 'tenant', 'created_at',
    )
    list_filter = ('status', 'category', 'priority', 'tenant')
    search_fields = ('ticket_number', 'subject', 'portal_account__display_name')
    inlines = [TicketMessageInline]


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = (
        'catalog_number', 'portal_name', 'category', 'unit_price',
        'stock_status', 'available_quantity', 'is_featured', 'is_active',
        'tenant', 'created_at',
    )
    list_filter = ('stock_status', 'is_featured', 'is_active', 'tenant')
    search_fields = ('catalog_number', 'portal_name', 'category')
