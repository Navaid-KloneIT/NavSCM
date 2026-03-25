from django.contrib import admin

from .models import (
    Carrier,
    FreightBill,
    FreightBillItem,
    LoadPlan,
    LoadPlanItem,
    RateCard,
    Route,
    Shipment,
    ShipmentItem,
    ShipmentTracking,
)


# =============================================================================
# CARRIER MANAGEMENT
# =============================================================================

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('carrier_number', 'name', 'carrier_type', 'email', 'phone', 'rating', 'is_active', 'tenant')
    list_filter = ('carrier_type', 'is_active', 'tenant')
    search_fields = ('carrier_number', 'name', 'email')


@admin.register(RateCard)
class RateCardAdmin(admin.ModelAdmin):
    list_display = ('rate_number', 'carrier', 'origin', 'destination', 'transport_mode', 'rate_per_unit', 'currency', 'is_active', 'tenant')
    list_filter = ('transport_mode', 'currency', 'is_active', 'tenant')
    search_fields = ('rate_number', 'carrier__name', 'origin', 'destination')


# =============================================================================
# ROUTE PLANNING
# =============================================================================

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_number', 'name', 'origin', 'destination', 'distance_km', 'transport_mode', 'status', 'tenant')
    list_filter = ('transport_mode', 'status', 'tenant')
    search_fields = ('route_number', 'name', 'origin', 'destination')


# =============================================================================
# SHIPMENT TRACKING
# =============================================================================

class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 1


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('shipment_number', 'carrier', 'status', 'priority', 'transport_mode', 'total_weight', 'tenant', 'created_at')
    list_filter = ('status', 'priority', 'transport_mode', 'tenant')
    search_fields = ('shipment_number', 'carrier__name')
    inlines = [ShipmentItemInline]


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'item', 'quantity', 'weight', 'volume')
    search_fields = ('item__name',)


@admin.register(ShipmentTracking)
class ShipmentTrackingAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'location', 'status', 'recorded_at', 'recorded_by')
    list_filter = ('status',)
    search_fields = ('shipment__shipment_number', 'location')


# =============================================================================
# FREIGHT AUDIT & PAYMENT
# =============================================================================

class FreightBillItemInline(admin.TabularInline):
    model = FreightBillItem
    extra = 1


@admin.register(FreightBill)
class FreightBillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'shipment', 'carrier', 'invoice_number', 'amount', 'currency', 'status', 'tenant', 'created_at')
    list_filter = ('status', 'currency', 'tenant')
    search_fields = ('bill_number', 'invoice_number', 'carrier__name')
    inlines = [FreightBillItemInline]


@admin.register(FreightBillItem)
class FreightBillItemAdmin(admin.ModelAdmin):
    list_display = ('freight_bill', 'description', 'charge_type', 'quantity', 'unit_price', 'total_price')
    search_fields = ('description',)


# =============================================================================
# LOAD OPTIMIZATION
# =============================================================================

class LoadPlanItemInline(admin.TabularInline):
    model = LoadPlanItem
    extra = 1


@admin.register(LoadPlan)
class LoadPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'vehicle_type', 'status', 'max_weight', 'planned_weight', 'utilization_percent', 'tenant', 'created_at')
    list_filter = ('vehicle_type', 'status', 'tenant')
    search_fields = ('plan_number',)
    inlines = [LoadPlanItemInline]


@admin.register(LoadPlanItem)
class LoadPlanItemAdmin(admin.ModelAdmin):
    list_display = ('load_plan', 'item', 'quantity', 'weight', 'volume', 'load_sequence')
    search_fields = ('item__name',)
