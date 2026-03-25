from django.contrib import admin

from .models import (
    AllocationItem,
    Backorder,
    Customer,
    CustomerNotification,
    Order,
    OrderAllocation,
    OrderItem,
    OrderValidation,
    SalesChannel,
)


# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_number', 'name', 'email', 'phone', 'company', 'credit_limit', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('customer_number', 'name', 'email', 'company')


@admin.register(SalesChannel)
class SalesChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_type', 'is_active', 'tenant')
    list_filter = ('channel_type', 'is_active', 'tenant')
    search_fields = ('name',)


# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'priority', 'order_date', 'total_amount', 'tenant', 'created_at')
    list_filter = ('status', 'priority', 'tenant')
    search_fields = ('order_number', 'customer__name')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'unit_price', 'total_price', 'status')
    search_fields = ('item__name',)


# =============================================================================
# ORDER VALIDATION
# =============================================================================

@admin.register(OrderValidation)
class OrderValidationAdmin(admin.ModelAdmin):
    list_display = ('validation_number', 'order', 'validation_type', 'status', 'validated_by', 'tenant', 'created_at')
    list_filter = ('validation_type', 'status', 'tenant')
    search_fields = ('validation_number', 'order__order_number')


# =============================================================================
# ORDER ALLOCATION
# =============================================================================

class AllocationItemInline(admin.TabularInline):
    model = AllocationItem
    extra = 1


@admin.register(OrderAllocation)
class OrderAllocationAdmin(admin.ModelAdmin):
    list_display = ('allocation_number', 'order', 'warehouse', 'allocation_method', 'status', 'tenant', 'created_at')
    list_filter = ('allocation_method', 'status', 'tenant')
    search_fields = ('allocation_number', 'order__order_number')
    inlines = [AllocationItemInline]


@admin.register(AllocationItem)
class AllocationItemAdmin(admin.ModelAdmin):
    list_display = ('allocation', 'item', 'requested_quantity', 'allocated_quantity', 'warehouse')
    search_fields = ('item__name',)


# =============================================================================
# BACKORDER MANAGEMENT
# =============================================================================

@admin.register(Backorder)
class BackorderAdmin(admin.ModelAdmin):
    list_display = ('backorder_number', 'order', 'item', 'quantity', 'fulfilled_quantity', 'status', 'expected_date', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('backorder_number', 'order__order_number', 'item__name')


# =============================================================================
# CUSTOMER NOTIFICATIONS
# =============================================================================

@admin.register(CustomerNotification)
class CustomerNotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_number', 'order', 'customer', 'notification_type', 'channel', 'status', 'tenant', 'created_at')
    list_filter = ('notification_type', 'channel', 'status', 'tenant')
    search_fields = ('notification_number', 'order__order_number', 'customer__name')
