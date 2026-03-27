from django.contrib import admin

from .models import (
    BillOfMaterials,
    BOMLineItem,
    MRPRequirement,
    MRPRun,
    ProductionLog,
    ProductionSchedule,
    ProductionScheduleItem,
    WorkCenter,
    WorkOrder,
    WorkOrderOperation,
)


# Inlines
class BOMLineItemInline(admin.TabularInline):
    model = BOMLineItem
    extra = 1


class ProductionScheduleItemInline(admin.TabularInline):
    model = ProductionScheduleItem
    extra = 1


class WorkOrderOperationInline(admin.TabularInline):
    model = WorkOrderOperation
    extra = 1


class MRPRequirementInline(admin.TabularInline):
    model = MRPRequirement
    extra = 0


# Main Admins
@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'work_center_type', 'hourly_capacity',
        'cost_per_hour', 'is_active', 'tenant',
    )
    list_filter = ('work_center_type', 'is_active', 'tenant')
    search_fields = ('code', 'name')


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = (
        'bom_number', 'title', 'product', 'version', 'status',
        'yield_quantity', 'created_by', 'tenant', 'created_at',
    )
    list_filter = ('status', 'tenant')
    search_fields = ('bom_number', 'title', 'product__name')
    inlines = [BOMLineItemInline]


@admin.register(ProductionSchedule)
class ProductionScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'schedule_number', 'title', 'status', 'start_date', 'end_date',
        'created_by', 'tenant', 'created_at',
    )
    list_filter = ('status', 'tenant')
    search_fields = ('schedule_number', 'title')
    inlines = [ProductionScheduleItemInline]


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order_number', 'product', 'status', 'priority',
        'planned_quantity', 'completed_quantity', 'work_center',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'priority', 'tenant')
    search_fields = ('work_order_number', 'product__name')
    inlines = [WorkOrderOperationInline]


@admin.register(MRPRun)
class MRPRunAdmin(admin.ModelAdmin):
    list_display = (
        'mrp_number', 'title', 'status', 'run_date',
        'planning_horizon_days', 'created_by', 'tenant', 'created_at',
    )
    list_filter = ('status', 'tenant')
    search_fields = ('mrp_number', 'title')
    inlines = [MRPRequirementInline]


@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = (
        'log_number', 'work_order', 'log_type', 'operator',
        'start_time', 'end_time', 'quantity_produced',
        'quantity_rejected', 'tenant',
    )
    list_filter = ('log_type', 'tenant')
    search_fields = ('log_number', 'work_order__work_order_number')
