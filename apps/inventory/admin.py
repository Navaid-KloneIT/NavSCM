from django.contrib import admin

from .models import (
    InventoryValuation,
    InventoryValuationItem,
    ReorderRule,
    ReorderSuggestion,
    StockAdjustment,
    StockAdjustmentItem,
    StockItem,
    Warehouse,
    WarehouseLocation,
    WarehouseTransfer,
    WarehouseTransferItem,
)


# =============================================================================
# FOUNDATION
# =============================================================================

class WarehouseLocationInline(admin.TabularInline):
    model = WarehouseLocation
    extra = 1


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'warehouse_type', 'city', 'is_active', 'tenant', 'created_at')
    list_filter = ('warehouse_type', 'is_active', 'tenant')
    search_fields = ('name', 'code', 'city')
    inlines = [WarehouseLocationInline]


@admin.register(WarehouseLocation)
class WarehouseLocationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'warehouse', 'zone', 'is_active', 'tenant')
    list_filter = ('zone', 'is_active', 'tenant')
    search_fields = ('name', 'code')


# =============================================================================
# STOCK CONTROL
# =============================================================================

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('item', 'warehouse', 'quantity_on_hand', 'quantity_reserved', 'unit_cost', 'tenant')
    list_filter = ('warehouse', 'tenant')
    search_fields = ('item__name', 'item__code', 'batch_number', 'serial_number')


# =============================================================================
# WAREHOUSE TRANSFER
# =============================================================================

class WarehouseTransferItemInline(admin.TabularInline):
    model = WarehouseTransferItem
    extra = 1


@admin.register(WarehouseTransfer)
class WarehouseTransferAdmin(admin.ModelAdmin):
    list_display = ('transfer_number', 'source_warehouse', 'destination_warehouse', 'status', 'tenant', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('transfer_number',)
    inlines = [WarehouseTransferItemInline]


@admin.register(WarehouseTransferItem)
class WarehouseTransferItemAdmin(admin.ModelAdmin):
    list_display = ('transfer', 'item', 'quantity_requested', 'quantity_sent', 'quantity_received')
    search_fields = ('item__name',)


# =============================================================================
# STOCK ADJUSTMENT
# =============================================================================

class StockAdjustmentItemInline(admin.TabularInline):
    model = StockAdjustmentItem
    extra = 1


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('adjustment_number', 'warehouse', 'adjustment_type', 'status', 'tenant', 'created_at')
    list_filter = ('adjustment_type', 'status', 'tenant')
    search_fields = ('adjustment_number',)
    inlines = [StockAdjustmentItemInline]


@admin.register(StockAdjustmentItem)
class StockAdjustmentItemAdmin(admin.ModelAdmin):
    list_display = ('adjustment', 'item', 'quantity_before', 'quantity_adjustment', 'quantity_after')
    search_fields = ('item__name',)


# =============================================================================
# REORDER AUTOMATION
# =============================================================================

@admin.register(ReorderRule)
class ReorderRuleAdmin(admin.ModelAdmin):
    list_display = ('item', 'warehouse', 'reorder_point', 'reorder_quantity', 'safety_stock', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('item__name', 'item__code')


@admin.register(ReorderSuggestion)
class ReorderSuggestionAdmin(admin.ModelAdmin):
    list_display = ('item', 'warehouse', 'suggested_quantity', 'current_stock', 'reorder_point', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('item__name',)


# =============================================================================
# INVENTORY VALUATION
# =============================================================================

class InventoryValuationItemInline(admin.TabularInline):
    model = InventoryValuationItem
    extra = 1


@admin.register(InventoryValuation)
class InventoryValuationAdmin(admin.ModelAdmin):
    list_display = ('valuation_number', 'warehouse', 'valuation_method', 'valuation_date', 'total_value', 'status', 'tenant')
    list_filter = ('valuation_method', 'status', 'tenant')
    search_fields = ('valuation_number',)
    inlines = [InventoryValuationItemInline]


@admin.register(InventoryValuationItem)
class InventoryValuationItemAdmin(admin.ModelAdmin):
    list_display = ('valuation', 'item', 'warehouse', 'quantity_on_hand', 'unit_cost', 'total_value')
    search_fields = ('item__name',)
