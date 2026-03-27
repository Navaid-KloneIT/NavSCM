from django import forms
from django.contrib.auth import get_user_model

from apps.procurement.models import Item
from apps.manufacturing.models import WorkOrder

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

User = get_user_model()


# =============================================================================
# INSPECTION TEMPLATE FORMS
# =============================================================================

class InspectionTemplateForm(forms.ModelForm):
    class Meta:
        model = InspectionTemplate
        fields = ['name', 'inspection_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'inspection_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class InspectionCriteriaForm(forms.ModelForm):
    class Meta:
        model = InspectionCriteria
        fields = [
            'sequence', 'name', 'description', 'acceptance_criteria',
            'measurement_type', 'is_required',
        ]
        widgets = {
            'sequence': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'acceptance_criteria': forms.TextInput(attrs={'class': 'form-control'}),
            'measurement_type': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


InspectionCriteriaFormSet = forms.inlineformset_factory(
    InspectionTemplate,
    InspectionCriteria,
    form=InspectionCriteriaForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# QUALITY INSPECTION FORMS
# =============================================================================

class QualityInspectionForm(forms.ModelForm):
    class Meta:
        model = QualityInspection
        fields = [
            'template', 'item', 'work_order', 'inspection_type',
            'inspector', 'inspection_date', 'lot_number', 'sample_size',
            'accepted_quantity', 'rejected_quantity', 'notes',
        ]
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'work_order': forms.Select(attrs={'class': 'form-select'}),
            'inspection_type': forms.Select(attrs={'class': 'form-select'}),
            'inspector': forms.Select(attrs={'class': 'form-select'}),
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'sample_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'accepted_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'rejected_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['template'].queryset = InspectionTemplate.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['work_order'].queryset = WorkOrder.objects.filter(
                tenant=tenant,
            ).exclude(status__in=['completed', 'cancelled'])
            self.fields['inspector'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['template'].queryset = InspectionTemplate.objects.none()
            self.fields['item'].queryset = Item.objects.none()
            self.fields['work_order'].queryset = WorkOrder.objects.none()
            self.fields['inspector'].queryset = User.objects.none()
        self.fields['template'].required = False
        self.fields['work_order'].required = False
        self.fields['inspector'].required = False


class InspectionResultForm(forms.ModelForm):
    class Meta:
        model = InspectionResult
        fields = ['criteria', 'result', 'measured_value', 'notes']
        widgets = {
            'criteria': forms.Select(attrs={'class': 'form-select'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'measured_value': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['criteria'].queryset = InspectionCriteria.objects.none()

        # If editing, populate criteria from the inspection's template
        if self.instance and self.instance.pk and self.instance.inspection:
            if self.instance.inspection.template:
                self.fields['criteria'].queryset = (
                    self.instance.inspection.template.criteria.all()
                )


InspectionResultFormSet = forms.inlineformset_factory(
    QualityInspection,
    InspectionResult,
    form=InspectionResultForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# NON-CONFORMANCE REPORT FORMS
# =============================================================================

class NonConformanceReportForm(forms.ModelForm):
    class Meta:
        model = NonConformanceReport
        fields = [
            'title', 'item', 'work_order', 'inspection', 'source',
            'severity', 'description', 'root_cause', 'disposition',
            'disposition_notes', 'quantity_affected', 'reported_by',
            'assigned_to', 'reported_date', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'work_order': forms.Select(attrs={'class': 'form-select'}),
            'inspection': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'root_cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'disposition': forms.Select(attrs={'class': 'form-select'}),
            'disposition_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantity_affected': forms.NumberInput(attrs={'class': 'form-control'}),
            'reported_by': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'reported_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['work_order'].queryset = WorkOrder.objects.filter(
                tenant=tenant,
            )
            self.fields['inspection'].queryset = QualityInspection.objects.filter(
                tenant=tenant,
            )
            self.fields['reported_by'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['item'].queryset = Item.objects.none()
            self.fields['work_order'].queryset = WorkOrder.objects.none()
            self.fields['inspection'].queryset = QualityInspection.objects.none()
            self.fields['reported_by'].queryset = User.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['item'].required = False
        self.fields['work_order'].required = False
        self.fields['inspection'].required = False
        self.fields['assigned_to'].required = False


# =============================================================================
# CAPA FORMS
# =============================================================================

class CAPAForm(forms.ModelForm):
    class Meta:
        model = CAPA
        fields = [
            'title', 'capa_type', 'ncr', 'priority', 'description',
            'root_cause_analysis', 'due_date', 'assigned_to', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'capa_type': forms.Select(attrs={'class': 'form-select'}),
            'ncr': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'root_cause_analysis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['ncr'].queryset = NonConformanceReport.objects.filter(
                tenant=tenant,
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['ncr'].queryset = NonConformanceReport.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['ncr'].required = False
        self.fields['assigned_to'].required = False


class CAPAActionForm(forms.ModelForm):
    class Meta:
        model = CAPAAction
        fields = ['sequence', 'description', 'assigned_to', 'due_date', 'status', 'notes']
        widgets = {
            'sequence': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['assigned_to'].queryset = User.objects.none()


CAPAActionFormSet = forms.inlineformset_factory(
    CAPA,
    CAPAAction,
    form=CAPAActionForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# QUALITY AUDIT FORMS
# =============================================================================

class QualityAuditForm(forms.ModelForm):
    class Meta:
        model = QualityAudit
        fields = ['title', 'audit_type', 'scope', 'lead_auditor', 'audit_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'audit_type': forms.Select(attrs={'class': 'form-select'}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'lead_auditor': forms.Select(attrs={'class': 'form-select'}),
            'audit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['lead_auditor'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['lead_auditor'].queryset = User.objects.none()
        self.fields['lead_auditor'].required = False


class AuditFindingForm(forms.ModelForm):
    class Meta:
        model = AuditFinding
        fields = [
            'finding_number', 'title', 'description', 'finding_type',
            'severity', 'assigned_to', 'due_date', 'corrective_action', 'notes',
        ]
        widgets = {
            'finding_number': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'finding_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'corrective_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['assigned_to'].queryset = User.objects.none()


AuditFindingFormSet = forms.inlineformset_factory(
    QualityAudit,
    AuditFinding,
    form=AuditFindingForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# CERTIFICATE OF ANALYSIS FORMS
# =============================================================================

class CertificateOfAnalysisForm(forms.ModelForm):
    class Meta:
        model = CertificateOfAnalysis
        fields = [
            'title', 'item', 'batch_number', 'production_date',
            'expiry_date', 'quantity', 'unit_of_measure', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'production_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['item'].queryset = Item.objects.none()


class CoATestResultForm(forms.ModelForm):
    class Meta:
        model = CoATestResult
        fields = [
            'sequence', 'test_name', 'test_method', 'specification',
            'result', 'unit_of_measure', 'status', 'notes',
        ]
        widgets = {
            'sequence': forms.NumberInput(attrs={'class': 'form-control'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'test_method': forms.TextInput(attrs={'class': 'form-control'}),
            'specification': forms.TextInput(attrs={'class': 'form-control'}),
            'result': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


CoATestResultFormSet = forms.inlineformset_factory(
    CertificateOfAnalysis,
    CoATestResult,
    form=CoATestResultForm,
    extra=1,
    can_delete=True,
)
