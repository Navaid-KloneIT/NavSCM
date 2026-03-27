from django.contrib import admin

from .models import (
    AuditFinding,
    CAPA,
    CAPAAction,
    CertificateOfAnalysis,
    CoATestResult,
    InspectionCriteria,
    InspectionResult,
    InspectionTemplate,
    NonConformanceReport,
    QualityAudit,
    QualityInspection,
)


# Inlines
class InspectionCriteriaInline(admin.TabularInline):
    model = InspectionCriteria
    extra = 1


class InspectionResultInline(admin.TabularInline):
    model = InspectionResult
    extra = 0


class CAPAActionInline(admin.TabularInline):
    model = CAPAAction
    extra = 1


class AuditFindingInline(admin.TabularInline):
    model = AuditFinding
    extra = 1


class CoATestResultInline(admin.TabularInline):
    model = CoATestResult
    extra = 1


# Main Admins
@admin.register(InspectionTemplate)
class InspectionTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'inspection_type', 'is_active', 'tenant', 'created_at',
    )
    list_filter = ('inspection_type', 'is_active', 'tenant')
    search_fields = ('name',)
    inlines = [InspectionCriteriaInline]


@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = (
        'inspection_number', 'item', 'inspection_type', 'status',
        'inspector', 'inspection_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'inspection_type', 'tenant')
    search_fields = ('inspection_number', 'item__name', 'lot_number')
    inlines = [InspectionResultInline]


@admin.register(NonConformanceReport)
class NonConformanceReportAdmin(admin.ModelAdmin):
    list_display = (
        'ncr_number', 'title', 'source', 'severity', 'status',
        'disposition', 'reported_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'severity', 'source', 'tenant')
    search_fields = ('ncr_number', 'title')


@admin.register(CAPA)
class CAPAAdmin(admin.ModelAdmin):
    list_display = (
        'capa_number', 'title', 'capa_type', 'status', 'priority',
        'due_date', 'assigned_to', 'tenant', 'created_at',
    )
    list_filter = ('status', 'capa_type', 'priority', 'tenant')
    search_fields = ('capa_number', 'title')
    inlines = [CAPAActionInline]


@admin.register(QualityAudit)
class QualityAuditAdmin(admin.ModelAdmin):
    list_display = (
        'audit_number', 'title', 'audit_type', 'status',
        'lead_auditor', 'audit_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'audit_type', 'tenant')
    search_fields = ('audit_number', 'title')
    inlines = [AuditFindingInline]


@admin.register(CertificateOfAnalysis)
class CertificateOfAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'coa_number', 'title', 'item', 'batch_number', 'status',
        'approved_by', 'tenant', 'created_at',
    )
    list_filter = ('status', 'tenant')
    search_fields = ('coa_number', 'title', 'batch_number')
    inlines = [CoATestResultInline]
