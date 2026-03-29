from django.contrib import admin

from .models import (
    ComplianceCheckItem,
    ComplianceRecord,
    Contract,
    ContractDocument,
    License,
    SustainabilityMetric,
    SustainabilityReport,
    TradeDocument,
    TradeDocumentItem,
)


# Inlines
class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 1


class ComplianceCheckItemInline(admin.TabularInline):
    model = ComplianceCheckItem
    extra = 1


class TradeDocumentItemInline(admin.TabularInline):
    model = TradeDocumentItem
    extra = 1


class SustainabilityMetricInline(admin.TabularInline):
    model = SustainabilityMetric
    extra = 1


# Main Admins
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        'contract_number', 'title', 'contract_type', 'vendor',
        'status', 'start_date', 'end_date', 'value', 'currency',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'contract_type', 'tenant')
    search_fields = ('contract_number', 'title', 'vendor__name')
    inlines = [ContractDocumentInline]


@admin.register(ComplianceRecord)
class ComplianceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'compliance_number', 'regulation_name', 'regulation_type',
        'status', 'risk_level', 'compliance_date', 'expiry_date',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'regulation_type', 'risk_level', 'tenant')
    search_fields = ('compliance_number', 'regulation_name')
    inlines = [ComplianceCheckItemInline]


@admin.register(TradeDocument)
class TradeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_number', 'document_type', 'vendor', 'status',
        'origin_country', 'destination_country', 'value', 'currency',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'document_type', 'tenant')
    search_fields = ('document_number', 'reference_number', 'vendor__name')
    inlines = [TradeDocumentItemInline]


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = (
        'license_number', 'title', 'license_type', 'issuing_authority',
        'status', 'issue_date', 'expiry_date', 'country',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'license_type', 'tenant')
    search_fields = ('license_number', 'title', 'issuing_authority')


@admin.register(SustainabilityReport)
class SustainabilityReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'title', 'report_type', 'status',
        'total_carbon_footprint', 'carbon_offset', 'sustainability_score',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'report_type', 'tenant')
    search_fields = ('report_number', 'title')
    inlines = [SustainabilityMetricInline]
