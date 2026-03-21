from django import forms

from apps.procurement.models import Item, Vendor

from .models import (
    CatalogItem,
    ContractMilestone,
    DueDiligenceCheck,
    QualificationQuestion,
    QualificationResponse,
    RiskFactor,
    ScorecardCriteria,
    ScorecardPeriod,
    SupplierCatalog,
    SupplierContract,
    SupplierOnboarding,
    SupplierRiskAssessment,
    SupplierScorecard,
)


# =============================================================================
# SUPPLIER ONBOARDING FORMS
# =============================================================================

class SupplierOnboardingForm(forms.ModelForm):
    class Meta:
        model = SupplierOnboarding
        fields = ['vendor', 'notes']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )


class QualificationQuestionForm(forms.ModelForm):
    class Meta:
        model = QualificationQuestion
        fields = ['category', 'question_text', 'is_required', 'is_active', 'order']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class QualificationResponseForm(forms.ModelForm):
    class Meta:
        model = QualificationResponse
        fields = ['question', 'response_text', 'attachments_note']
        widgets = {
            'question': forms.Select(attrs={'class': 'form-select'}),
            'response_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'attachments_note': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['question'].queryset = QualificationQuestion.objects.filter(
                tenant=tenant, is_active=True
            )


QualificationResponseFormSet = forms.inlineformset_factory(
    SupplierOnboarding,
    QualificationResponse,
    form=QualificationResponseForm,
    extra=3,
    can_delete=True,
)


class DueDiligenceCheckForm(forms.ModelForm):
    class Meta:
        model = DueDiligenceCheck
        fields = ['check_type', 'description', 'status', 'notes', 'attachments_note']
        widgets = {
            'check_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
            'attachments_note': forms.TextInput(attrs={'class': 'form-control'}),
        }


DueDiligenceCheckFormSet = forms.inlineformset_factory(
    SupplierOnboarding,
    DueDiligenceCheck,
    form=DueDiligenceCheckForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# SUPPLIER SCORECARD FORMS
# =============================================================================

class ScorecardPeriodForm(forms.ModelForm):
    class Meta:
        model = ScorecardPeriod
        fields = ['name', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SupplierScorecardForm(forms.ModelForm):
    class Meta:
        model = SupplierScorecard
        fields = [
            'vendor', 'period', 'delivery_score', 'quality_score',
            'price_score', 'responsiveness_score', 'rating', 'notes',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'delivery_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'quality_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'price_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'responsiveness_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['period'].queryset = ScorecardPeriod.objects.filter(
                tenant=tenant, is_active=True
            )


class ScorecardCriteriaForm(forms.ModelForm):
    class Meta:
        model = ScorecardCriteria
        fields = ['category', 'criteria_name', 'weight', 'score', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'criteria_name': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


ScorecardCriteriaFormSet = forms.inlineformset_factory(
    SupplierScorecard,
    ScorecardCriteria,
    form=ScorecardCriteriaForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# CONTRACT MANAGEMENT FORMS
# =============================================================================

class SupplierContractForm(forms.ModelForm):
    class Meta:
        model = SupplierContract
        fields = [
            'vendor', 'title', 'description', 'contract_type',
            'start_date', 'end_date', 'value', 'currency',
            'payment_terms', 'auto_renew', 'renewal_notice_days',
            'terms_conditions', 'notes',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'renewal_notice_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )


class ContractMilestoneForm(forms.ModelForm):
    class Meta:
        model = ContractMilestone
        fields = ['title', 'description', 'due_date', 'status', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


ContractMilestoneFormSet = forms.inlineformset_factory(
    SupplierContract,
    ContractMilestone,
    form=ContractMilestoneForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# SUPPLIER CATALOG FORMS
# =============================================================================

class SupplierCatalogForm(forms.ModelForm):
    class Meta:
        model = SupplierCatalog
        fields = ['vendor', 'name', 'description', 'effective_date', 'expiry_date', 'notes']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )


class CatalogItemForm(forms.ModelForm):
    class Meta:
        model = CatalogItem
        fields = [
            'item', 'supplier_part_number', 'description',
            'unit_of_measure', 'unit_price', 'min_order_quantity',
            'lead_time_days', 'is_active', 'notes',
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'supplier_part_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'min_order_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True
            )
        self.fields['item'].required = False


CatalogItemFormSet = forms.inlineformset_factory(
    SupplierCatalog,
    CatalogItem,
    form=CatalogItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# RISK MANAGEMENT FORMS
# =============================================================================

class SupplierRiskAssessmentForm(forms.ModelForm):
    class Meta:
        model = SupplierRiskAssessment
        fields = ['vendor', 'assessment_date', 'overall_risk_level', 'notes']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'assessment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'overall_risk_level': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )


class RiskFactorForm(forms.ModelForm):
    class Meta:
        model = RiskFactor
        fields = [
            'category', 'factor_name', 'description',
            'likelihood', 'impact', 'mitigation_plan', 'status', 'notes',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'factor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'likelihood': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'impact': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'mitigation_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


RiskFactorFormSet = forms.inlineformset_factory(
    SupplierRiskAssessment,
    RiskFactor,
    form=RiskFactorForm,
    extra=1,
    can_delete=True,
)
