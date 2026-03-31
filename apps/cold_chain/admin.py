from django.contrib import admin

from .models import (
    ColdStorageItem,
    ColdStorageUnit,
    ComplianceReport,
    ComplianceReportItem,
    ReeferMaintenance,
    ReeferUnit,
    TemperatureExcursion,
    TemperatureReading,
    TemperatureSensor,
    TemperatureZone,
)


# Inlines
class TemperatureReadingInline(admin.TabularInline):
    model = TemperatureReading
    extra = 1


class ColdStorageItemInline(admin.TabularInline):
    model = ColdStorageItem
    extra = 1


class ComplianceReportItemInline(admin.TabularInline):
    model = ComplianceReportItem
    extra = 1


# Main Admins
@admin.register(TemperatureSensor)
class TemperatureSensorAdmin(admin.ModelAdmin):
    list_display = (
        'sensor_number', 'name', 'sensor_type', 'location_type',
        'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'sensor_type', 'location_type', 'tenant')
    search_fields = ('sensor_number', 'name', 'serial_number')
    inlines = [TemperatureReadingInline]


@admin.register(TemperatureZone)
class TemperatureZoneAdmin(admin.ModelAdmin):
    list_display = (
        'zone_number', 'name', 'zone_type', 'min_temperature',
        'max_temperature', 'status', 'tenant',
    )
    list_filter = ('status', 'zone_type', 'tenant')
    search_fields = ('zone_number', 'name')


@admin.register(TemperatureExcursion)
class TemperatureExcursionAdmin(admin.ModelAdmin):
    list_display = (
        'excursion_number', 'severity', 'status', 'sensor', 'zone',
        'temperature_recorded', 'detected_at', 'tenant',
    )
    list_filter = ('status', 'severity', 'tenant')
    search_fields = ('excursion_number',)


@admin.register(ColdStorageUnit)
class ColdStorageUnitAdmin(admin.ModelAdmin):
    list_display = (
        'unit_number', 'name', 'unit_type', 'status',
        'current_temperature', 'zone', 'tenant',
    )
    list_filter = ('status', 'unit_type', 'tenant')
    search_fields = ('unit_number', 'name', 'serial_number')
    inlines = [ColdStorageItemInline]


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'title', 'report_type', 'status',
        'regulatory_body', 'period_start', 'period_end', 'tenant',
    )
    list_filter = ('status', 'report_type', 'regulatory_body', 'tenant')
    search_fields = ('report_number', 'title')
    inlines = [ComplianceReportItemInline]


@admin.register(ReeferUnit)
class ReeferUnitAdmin(admin.ModelAdmin):
    list_display = (
        'unit_number', 'name', 'unit_type', 'refrigerant_type',
        'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'unit_type', 'refrigerant_type', 'tenant')
    search_fields = ('unit_number', 'name', 'serial_number')


@admin.register(ReeferMaintenance)
class ReeferMaintenanceAdmin(admin.ModelAdmin):
    list_display = (
        'maintenance_number', 'title', 'reefer', 'maintenance_type',
        'priority', 'status', 'scheduled_date', 'tenant',
    )
    list_filter = ('status', 'maintenance_type', 'priority', 'tenant')
    search_fields = ('maintenance_number', 'title')
