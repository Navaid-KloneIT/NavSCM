from django.contrib import admin

from .models import (
    GoodsReceiptNote,
    GRNItem,
    Item,
    ItemCategory,
    POAcknowledgement,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RFQ,
    RFQItem,
    RFQVendor,
    ShipmentUpdate,
    ThreeWayMatch,
    Vendor,
    VendorContact,
    VendorInvoice,
    VendorInvoiceItem,
    VendorQuote,
)


# =============================================================================
# FOUNDATION
# =============================================================================

@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'tenant', 'is_active', 'created_at')
    list_filter = ('is_active', 'tenant')
    search_fields = ('name',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'unit_of_measure', 'unit_price', 'is_active', 'tenant')
    list_filter = ('is_active', 'unit_of_measure', 'tenant')
    search_fields = ('name', 'code')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'contact_person', 'email', 'payment_terms', 'is_active', 'tenant')
    list_filter = ('is_active', 'payment_terms', 'tenant')
    search_fields = ('name', 'code', 'email', 'contact_person')


# =============================================================================
# PURCHASE REQUISITION
# =============================================================================

class PurchaseRequisitionItemInline(admin.TabularInline):
    model = PurchaseRequisitionItem
    extra = 1


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ('requisition_number', 'title', 'status', 'priority', 'requested_by', 'tenant', 'created_at')
    list_filter = ('status', 'priority', 'tenant')
    search_fields = ('requisition_number', 'title')
    inlines = [PurchaseRequisitionItemInline]


# =============================================================================
# RFQ
# =============================================================================

class RFQItemInline(admin.TabularInline):
    model = RFQItem
    extra = 1


class RFQVendorInline(admin.TabularInline):
    model = RFQVendor
    extra = 1


@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ('rfq_number', 'title', 'status', 'submission_deadline', 'created_by', 'tenant', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('rfq_number', 'title')
    inlines = [RFQItemInline, RFQVendorInline]


@admin.register(VendorQuote)
class VendorQuoteAdmin(admin.ModelAdmin):
    list_display = ('rfq_vendor', 'rfq_item', 'unit_price', 'total_price', 'lead_time_days', 'is_selected')
    list_filter = ('is_selected',)


# =============================================================================
# PURCHASE ORDER
# =============================================================================

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'status', 'total_amount', 'order_date', 'tenant', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('po_number', 'vendor__name')
    inlines = [PurchaseOrderItemInline]


# =============================================================================
# VENDOR PORTAL
# =============================================================================

@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'email', 'is_primary', 'is_active', 'tenant')
    list_filter = ('is_active', 'is_primary', 'tenant')
    search_fields = ('name', 'email')


@admin.register(POAcknowledgement)
class POAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'acknowledged_by', 'acknowledged_at', 'expected_delivery_date')


@admin.register(ShipmentUpdate)
class ShipmentUpdateAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'status', 'tracking_number', 'carrier', 'estimated_arrival', 'created_at')
    list_filter = ('status',)


# =============================================================================
# INVOICE RECONCILIATION
# =============================================================================

class GRNItemInline(admin.TabularInline):
    model = GRNItem
    extra = 1


@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(admin.ModelAdmin):
    list_display = ('grn_number', 'purchase_order', 'status', 'received_by', 'received_date', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('grn_number',)
    inlines = [GRNItemInline]


class VendorInvoiceItemInline(admin.TabularInline):
    model = VendorInvoiceItem
    extra = 1


@admin.register(VendorInvoice)
class VendorInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'vendor', 'status', 'total_amount', 'invoice_date', 'due_date', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('invoice_number', 'vendor__name')
    inlines = [VendorInvoiceItemInline]


@admin.register(ThreeWayMatch)
class ThreeWayMatchAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'purchase_order', 'grn', 'match_status', 'quantity_match', 'price_match', 'total_match', 'created_at')
    list_filter = ('match_status', 'tenant')
