from django.contrib import admin

from .models import (
    CollaborativePlan,
    DemandSignal,
    ForecastLineItem,
    PlanComment,
    PlanLineItem,
    PromotionalEvent,
    SafetyStockCalculation,
    SafetyStockItem,
    SalesForecast,
    SeasonalityProfile,
)


# Inlines
class ForecastLineItemInline(admin.TabularInline):
    model = ForecastLineItem
    extra = 1


class PlanLineItemInline(admin.TabularInline):
    model = PlanLineItem
    extra = 1


class PlanCommentInline(admin.TabularInline):
    model = PlanComment
    extra = 0


class SafetyStockItemInline(admin.TabularInline):
    model = SafetyStockItem
    extra = 1


class PromotionalEventInline(admin.TabularInline):
    model = PromotionalEvent
    extra = 0


# Main Admins
@admin.register(SalesForecast)
class SalesForecastAdmin(admin.ModelAdmin):
    list_display = (
        'forecast_number', 'title', 'forecast_method', 'status',
        'start_date', 'end_date', 'created_by', 'tenant', 'created_at',
    )
    list_filter = ('status', 'forecast_method', 'tenant')
    search_fields = ('forecast_number', 'title')
    inlines = [ForecastLineItemInline]


@admin.register(SeasonalityProfile)
class SeasonalityProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'item', 'is_active', 'tenant', 'created_at')
    list_filter = ('is_active', 'tenant')
    search_fields = ('name', 'item__name')
    inlines = [PromotionalEventInline]


@admin.register(PromotionalEvent)
class PromotionalEventAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'event_type', 'start_date', 'end_date',
        'impact_factor', 'is_active', 'tenant',
    )
    list_filter = ('event_type', 'is_active', 'tenant')
    search_fields = ('name',)


@admin.register(DemandSignal)
class DemandSignalAdmin(admin.ModelAdmin):
    list_display = (
        'signal_number', 'title', 'signal_type', 'impact_level',
        'status', 'signal_date', 'tenant', 'created_at',
    )
    list_filter = ('signal_type', 'impact_level', 'status', 'tenant')
    search_fields = ('signal_number', 'title')


@admin.register(CollaborativePlan)
class CollaborativePlanAdmin(admin.ModelAdmin):
    list_display = (
        'plan_number', 'title', 'plan_type', 'status',
        'start_date', 'end_date', 'created_by', 'tenant', 'created_at',
    )
    list_filter = ('plan_type', 'status', 'tenant')
    search_fields = ('plan_number', 'title')
    inlines = [PlanLineItemInline, PlanCommentInline]


@admin.register(SafetyStockCalculation)
class SafetyStockCalculationAdmin(admin.ModelAdmin):
    list_display = (
        'calculation_number', 'title', 'calculation_method', 'status',
        'calculation_date', 'created_by', 'tenant', 'created_at',
    )
    list_filter = ('calculation_method', 'status', 'tenant')
    search_fields = ('calculation_number', 'title')
    inlines = [SafetyStockItemInline]
