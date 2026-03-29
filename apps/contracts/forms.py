from django import forms
from django.contrib.auth import get_user_model

from apps.procurement.models import Vendor

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

User = get_user_model()


# =============================================================================
# CONTRACT FORMS
# =============================================================================

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'title', 'contract_type', 'vendor', 'start_date', 'end_date',
            'value', 'currency', 'description', 'terms_and_conditions',
            'auto_renew', 'renewal_period_days', 'notice_period_days',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'renewal_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'notice_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['vendor'].queryset = Vendor.objects.none()
        self.fields['vendor'].required = False


class ContractDocumentForm(forms.ModelForm):
    class Meta:
        model = ContractDocument
        fields = ['document_name', 'description', 'file_reference']
        widgets = {
            'document_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'file_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }


ContractDocumentFormSet = forms.inlineformset_factory(
    Contract,
    ContractDocument,
    form=ContractDocumentForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# COMPLIANCE RECORD FORMS
# =============================================================================

class ComplianceRecordForm(forms.ModelForm):
    class Meta:
        model = ComplianceRecord
        fields = [
            'regulation_name', 'regulation_type', 'compliance_date',
            'expiry_date', 'responsible_person', 'description',
            'corrective_action', 'risk_level',
        ]
        widgets = {
            'regulation_name': forms.TextInput(attrs={'class': 'form-control'}),
            'regulation_type': forms.Select(attrs={'class': 'form-select'}),
            'compliance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'corrective_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['responsible_person'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['responsible_person'].queryset = User.objects.none()
        self.fields['responsible_person'].required = False


class ComplianceCheckItemForm(forms.ModelForm):
    class Meta:
        model = ComplianceCheckItem
        fields = ['check_item', 'result', 'notes']
        widgets = {
            'check_item': forms.TextInput(attrs={'class': 'form-control'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


ComplianceCheckItemFormSet = forms.inlineformset_factory(
    ComplianceRecord,
    ComplianceCheckItem,
    form=ComplianceCheckItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# TRADE DOCUMENT FORMS
# =============================================================================

class TradeDocumentForm(forms.ModelForm):
    class Meta:
        model = TradeDocument
        fields = [
            'document_type', 'vendor', 'origin_country', 'destination_country',
            'issue_date', 'reference_number', 'value', 'currency',
            'description', 'notes',
        ]
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'origin_country': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_country': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['vendor'].queryset = Vendor.objects.none()
        self.fields['vendor'].required = False


class TradeDocumentItemForm(forms.ModelForm):
    class Meta:
        model = TradeDocumentItem
        fields = ['item_description', 'quantity', 'unit_value', 'total_value']
        widgets = {
            'item_description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


TradeDocumentItemFormSet = forms.inlineformset_factory(
    TradeDocument,
    TradeDocumentItem,
    form=TradeDocumentItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# LICENSE FORMS
# =============================================================================

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = [
            'title', 'license_type', 'issuing_authority', 'issue_date',
            'expiry_date', 'license_reference', 'country', 'description',
            'renewal_notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'license_type': forms.Select(attrs={'class': 'form-select'}),
            'issuing_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'license_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'renewal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# SUSTAINABILITY REPORT FORMS
# =============================================================================

class SustainabilityReportForm(forms.ModelForm):
    class Meta:
        model = SustainabilityReport
        fields = [
            'title', 'report_type', 'period_start', 'period_end',
            'total_carbon_footprint', 'carbon_offset', 'sustainability_score',
            'description', 'recommendations',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_carbon_footprint': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'carbon_offset': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sustainability_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SustainabilityMetricForm(forms.ModelForm):
    class Meta:
        model = SustainabilityMetric
        fields = ['metric_name', 'value', 'unit', 'target', 'variance']
        widgets = {
            'metric_name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'variance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


SustainabilityMetricFormSet = forms.inlineformset_factory(
    SustainabilityReport,
    SustainabilityMetric,
    form=SustainabilityMetricForm,
    extra=1,
    can_delete=True,
)
