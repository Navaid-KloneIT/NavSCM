from django.contrib import admin

from .models import (
    FinancialReport,
    FinancialReportItem,
    InventoryAnalytics,
    InventoryAnalyticsItem,
    LogisticsKPI,
    LogisticsKPIItem,
    PredictiveAlert,
    ProcurementAnalytics,
    ProcurementAnalyticsItem,
)


# Inlines
class InventoryAnalyticsItemInline(admin.TabularInline):
    model = InventoryAnalyticsItem
    extra = 1


class ProcurementAnalyticsItemInline(admin.TabularInline):
    model = ProcurementAnalyticsItem
    extra = 1


class LogisticsKPIItemInline(admin.TabularInline):
    model = LogisticsKPIItem
    extra = 1


class FinancialReportItemInline(admin.TabularInline):
    model = FinancialReportItem
    extra = 1


# Main Admins
@admin.register(InventoryAnalytics)
class InventoryAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'report_type', 'status', 'start_date',
        'end_date', 'total_items', 'total_value', 'tenant', 'created_at',
    )
    list_filter = ('status', 'report_type', 'tenant')
    search_fields = ('report_number',)
    inlines = [InventoryAnalyticsItemInline]


@admin.register(ProcurementAnalytics)
class ProcurementAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'report_type', 'status', 'start_date',
        'end_date', 'total_spend', 'total_orders', 'tenant', 'created_at',
    )
    list_filter = ('status', 'report_type', 'tenant')
    search_fields = ('report_number',)
    inlines = [ProcurementAnalyticsItemInline]


@admin.register(LogisticsKPI)
class LogisticsKPIAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'report_type', 'status', 'start_date',
        'end_date', 'total_shipments', 'on_time_rate', 'tenant', 'created_at',
    )
    list_filter = ('status', 'report_type', 'tenant')
    search_fields = ('report_number',)
    inlines = [LogisticsKPIItemInline]


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'report_type', 'status', 'start_date',
        'end_date', 'total_revenue', 'gross_margin_percentage', 'tenant', 'created_at',
    )
    list_filter = ('status', 'report_type', 'tenant')
    search_fields = ('report_number',)
    inlines = [FinancialReportItemInline]


@admin.register(PredictiveAlert)
class PredictiveAlertAdmin(admin.ModelAdmin):
    list_display = (
        'alert_number', 'title', 'alert_type', 'severity', 'status',
        'predicted_date', 'confidence_level', 'tenant', 'created_at',
    )
    list_filter = ('status', 'alert_type', 'severity', 'tenant')
    search_fields = ('alert_number', 'title')
