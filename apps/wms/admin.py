from django.contrib import admin

from .models import (
    Bin,
    CycleCount,
    CycleCountItem,
    CycleCountPlan,
    DockAppointment,
    PackingOrder,
    PickList,
    PickListItem,
    PutAwayTask,
    ReceivingOrder,
    ReceivingOrderItem,
    ShippingLabel,
    YardLocation,
    YardVisit,
)


# =============================================================================
# BIN MANAGEMENT
# =============================================================================

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('bin_code', 'warehouse', 'zone', 'bin_type', 'capacity', 'current_utilization', 'is_active', 'tenant')
    list_filter = ('bin_type', 'is_active', 'tenant')
    search_fields = ('bin_code', 'zone', 'aisle')


# =============================================================================
# INBOUND OPERATIONS
# =============================================================================

@admin.register(DockAppointment)
class DockAppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_number', 'warehouse', 'dock_number', 'appointment_date', 'time_slot', 'carrier_name', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('appointment_number', 'carrier_name')


class ReceivingOrderItemInline(admin.TabularInline):
    model = ReceivingOrderItem
    extra = 1


@admin.register(ReceivingOrder)
class ReceivingOrderAdmin(admin.ModelAdmin):
    list_display = ('receiving_number', 'warehouse', 'supplier_name', 'status', 'tenant', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('receiving_number', 'supplier_name', 'po_reference')
    inlines = [ReceivingOrderItemInline]


@admin.register(ReceivingOrderItem)
class ReceivingOrderItemAdmin(admin.ModelAdmin):
    list_display = ('receiving_order', 'item', 'expected_quantity', 'received_quantity', 'damaged_quantity')
    search_fields = ('item__name',)


@admin.register(PutAwayTask)
class PutAwayTaskAdmin(admin.ModelAdmin):
    list_display = ('task_number', 'receiving_order', 'item', 'quantity', 'status', 'assigned_to', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('task_number',)


# =============================================================================
# OUTBOUND OPERATIONS
# =============================================================================

class PickListItemInline(admin.TabularInline):
    model = PickListItem
    extra = 1


@admin.register(PickList)
class PickListAdmin(admin.ModelAdmin):
    list_display = ('pick_number', 'warehouse', 'pick_type', 'status', 'priority', 'assigned_to', 'tenant', 'created_at')
    list_filter = ('pick_type', 'status', 'priority', 'tenant')
    search_fields = ('pick_number',)
    inlines = [PickListItemInline]


@admin.register(PickListItem)
class PickListItemAdmin(admin.ModelAdmin):
    list_display = ('pick_list', 'item', 'quantity_requested', 'quantity_picked', 'status')
    search_fields = ('item__name',)


@admin.register(PackingOrder)
class PackingOrderAdmin(admin.ModelAdmin):
    list_display = ('packing_number', 'warehouse', 'pick_list', 'status', 'total_packages', 'tenant', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('packing_number', 'tracking_number')


@admin.register(ShippingLabel)
class ShippingLabelAdmin(admin.ModelAdmin):
    list_display = ('label_number', 'packing_order', 'carrier', 'tracking_number', 'weight', 'tenant')
    list_filter = ('carrier', 'tenant')
    search_fields = ('label_number', 'tracking_number')


# =============================================================================
# CYCLE COUNTING
# =============================================================================

@admin.register(CycleCountPlan)
class CycleCountPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'name', 'warehouse', 'count_type', 'frequency', 'status', 'tenant')
    list_filter = ('count_type', 'frequency', 'status', 'tenant')
    search_fields = ('plan_number', 'name')


class CycleCountItemInline(admin.TabularInline):
    model = CycleCountItem
    extra = 1


@admin.register(CycleCount)
class CycleCountAdmin(admin.ModelAdmin):
    list_display = ('count_number', 'warehouse', 'plan', 'status', 'counter', 'total_items', 'items_counted', 'variance_count', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('count_number',)
    inlines = [CycleCountItemInline]


@admin.register(CycleCountItem)
class CycleCountItemAdmin(admin.ModelAdmin):
    list_display = ('cycle_count', 'item', 'bin', 'expected_quantity', 'counted_quantity', 'variance')
    search_fields = ('item__name',)


# =============================================================================
# YARD MANAGEMENT
# =============================================================================

@admin.register(YardLocation)
class YardLocationAdmin(admin.ModelAdmin):
    list_display = ('location_code', 'warehouse', 'location_type', 'is_occupied', 'is_active', 'tenant')
    list_filter = ('location_type', 'is_occupied', 'is_active', 'tenant')
    search_fields = ('location_code',)


@admin.register(YardVisit)
class YardVisitAdmin(admin.ModelAdmin):
    list_display = ('visit_number', 'warehouse', 'carrier_name', 'visit_type', 'status', 'yard_location', 'tenant')
    list_filter = ('visit_type', 'status', 'tenant')
    search_fields = ('visit_number', 'carrier_name', 'driver_name', 'trailer_number')
