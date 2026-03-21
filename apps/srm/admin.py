from django.contrib import admin

from .models import (
    CatalogItem,
    ContractDocument,
    ContractMilestone,
    DueDiligenceCheck,
    QualificationQuestion,
    QualificationResponse,
    RiskFactor,
    RiskMitigationAction,
    ScorecardCriteria,
    ScorecardPeriod,
    SupplierCatalog,
    SupplierContract,
    SupplierOnboarding,
    SupplierRiskAssessment,
    SupplierScorecard,
)


# =============================================================================
# SUPPLIER ONBOARDING
# =============================================================================

class QualificationResponseInline(admin.TabularInline):
    model = QualificationResponse
    extra = 1


class DueDiligenceCheckInline(admin.TabularInline):
    model = DueDiligenceCheck
    extra = 1


@admin.register(SupplierOnboarding)
class SupplierOnboardingAdmin(admin.ModelAdmin):
    list_display = ('onboarding_number', 'vendor', 'status', 'submitted_by', 'tenant', 'created_at')
    list_filter = ('status', 'tenant')
    search_fields = ('onboarding_number', 'vendor__name')
    inlines = [QualificationResponseInline, DueDiligenceCheckInline]


@admin.register(QualificationQuestion)
class QualificationQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'category', 'is_required', 'is_active', 'order', 'tenant')
    list_filter = ('category', 'is_required', 'is_active', 'tenant')
    search_fields = ('question_text',)


# =============================================================================
# SUPPLIER SCORECARD
# =============================================================================

class ScorecardCriteriaInline(admin.TabularInline):
    model = ScorecardCriteria
    extra = 1


@admin.register(ScorecardPeriod)
class ScorecardPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('name',)


@admin.register(SupplierScorecard)
class SupplierScorecardAdmin(admin.ModelAdmin):
    list_display = ('scorecard_number', 'vendor', 'period', 'overall_score', 'rating', 'status', 'tenant', 'created_at')
    list_filter = ('status', 'rating', 'tenant')
    search_fields = ('scorecard_number', 'vendor__name')
    inlines = [ScorecardCriteriaInline]


# =============================================================================
# CONTRACT MANAGEMENT
# =============================================================================

class ContractMilestoneInline(admin.TabularInline):
    model = ContractMilestone
    extra = 1


class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 1


@admin.register(SupplierContract)
class SupplierContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'vendor', 'title', 'contract_type', 'status', 'value', 'start_date', 'end_date', 'tenant')
    list_filter = ('status', 'contract_type', 'tenant')
    search_fields = ('contract_number', 'title', 'vendor__name')
    inlines = [ContractMilestoneInline, ContractDocumentInline]


# =============================================================================
# SUPPLIER CATALOG
# =============================================================================

class CatalogItemInline(admin.TabularInline):
    model = CatalogItem
    extra = 1


@admin.register(SupplierCatalog)
class SupplierCatalogAdmin(admin.ModelAdmin):
    list_display = ('catalog_number', 'vendor', 'name', 'status', 'effective_date', 'expiry_date', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('catalog_number', 'name', 'vendor__name')
    inlines = [CatalogItemInline]


# =============================================================================
# RISK MANAGEMENT
# =============================================================================

class RiskFactorInline(admin.TabularInline):
    model = RiskFactor
    extra = 1


class RiskMitigationActionInline(admin.TabularInline):
    model = RiskMitigationAction
    extra = 1


@admin.register(SupplierRiskAssessment)
class SupplierRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('assessment_number', 'vendor', 'assessment_date', 'overall_risk_level', 'overall_risk_score', 'status', 'tenant')
    list_filter = ('status', 'overall_risk_level', 'tenant')
    search_fields = ('assessment_number', 'vendor__name')
    inlines = [RiskFactorInline]


@admin.register(RiskFactor)
class RiskFactorAdmin(admin.ModelAdmin):
    list_display = ('factor_name', 'category', 'likelihood', 'impact', 'risk_score', 'status', 'assessment')
    list_filter = ('category', 'status')
    search_fields = ('factor_name',)
    inlines = [RiskMitigationActionInline]
