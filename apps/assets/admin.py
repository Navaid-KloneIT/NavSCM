from django.contrib import admin

from .models import (
    Asset,
    AssetDepreciation,
    AssetSpecification,
    BreakdownMaintenance,
    MaintenanceTask,
    PreventiveMaintenance,
    SparePart,
    SparePartUsage,
)


# Inlines
class AssetSpecificationInline(admin.TabularInline):
    model = AssetSpecification
    extra = 1


class MaintenanceTaskInline(admin.TabularInline):
    model = MaintenanceTask
    extra = 1


class SparePartUsageInline(admin.TabularInline):
    model = SparePartUsage
    extra = 1


# Main Admins
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_number', 'name', 'asset_type', 'status', 'condition',
        'location', 'purchase_cost', 'tenant', 'created_at',
    )
    list_filter = ('status', 'asset_type', 'condition', 'tenant')
    search_fields = ('asset_number', 'name', 'serial_number')
    inlines = [AssetSpecificationInline]


@admin.register(PreventiveMaintenance)
class PreventiveMaintenanceAdmin(admin.ModelAdmin):
    list_display = (
        'pm_number', 'asset', 'title', 'frequency', 'priority',
        'status', 'scheduled_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'frequency', 'priority', 'tenant')
    search_fields = ('pm_number', 'title', 'asset__name')
    inlines = [MaintenanceTaskInline]


@admin.register(BreakdownMaintenance)
class BreakdownMaintenanceAdmin(admin.ModelAdmin):
    list_display = (
        'bm_number', 'asset', 'title', 'severity', 'status',
        'downtime_hours', 'repair_cost', 'tenant', 'created_at',
    )
    list_filter = ('status', 'severity', 'tenant')
    search_fields = ('bm_number', 'title', 'asset__name')


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = (
        'part_number', 'name', 'category', 'quantity_on_hand',
        'reorder_level', 'unit_cost', 'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'tenant')
    search_fields = ('part_number', 'name', 'category')
    inlines = [SparePartUsageInline]


@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(admin.ModelAdmin):
    list_display = (
        'depreciation_number', 'asset', 'method', 'status',
        'original_cost', 'current_book_value', 'annual_depreciation',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'method', 'tenant')
    search_fields = ('depreciation_number', 'asset__name')
