from django import forms
from django.contrib.auth import get_user_model

from apps.procurement.models import Vendor

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

User = get_user_model()


# =============================================================================
# ASSET REGISTRY FORMS
# =============================================================================

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'name', 'asset_type', 'condition', 'manufacturer', 'model_number',
            'serial_number', 'purchase_date', 'purchase_cost', 'currency',
            'warranty_expiry', 'location', 'assigned_to', 'description', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_type': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['assigned_to'].required = False


class AssetSpecificationForm(forms.ModelForm):
    class Meta:
        model = AssetSpecification
        fields = ['spec_name', 'spec_value', 'unit']
        widgets = {
            'spec_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spec_value': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
        }


AssetSpecificationFormSet = forms.inlineformset_factory(
    Asset,
    AssetSpecification,
    form=AssetSpecificationForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PREVENTIVE MAINTENANCE FORMS
# =============================================================================

class PreventiveMaintenanceForm(forms.ModelForm):
    class Meta:
        model = PreventiveMaintenance
        fields = [
            'asset', 'title', 'frequency', 'priority', 'scheduled_date',
            'next_due_date', 'estimated_duration_hours', 'estimated_cost',
            'assigned_to', 'description', 'notes',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.objects.filter(
                tenant=tenant,
            ).exclude(status__in=['retired', 'disposed'])
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['asset'].queryset = Asset.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['assigned_to'].required = False


class MaintenanceTaskForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ['task_name', 'status', 'notes']
        widgets = {
            'task_name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


MaintenanceTaskFormSet = forms.inlineformset_factory(
    PreventiveMaintenance,
    MaintenanceTask,
    form=MaintenanceTaskForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# BREAKDOWN MAINTENANCE FORMS
# =============================================================================

class BreakdownMaintenanceForm(forms.ModelForm):
    class Meta:
        model = BreakdownMaintenance
        fields = [
            'asset', 'title', 'severity', 'downtime_hours', 'repair_cost',
            'root_cause', 'repair_description', 'assigned_to',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'downtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'repair_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'root_cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'repair_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.objects.filter(
                tenant=tenant,
            ).exclude(status__in=['retired', 'disposed'])
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['asset'].queryset = Asset.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['assigned_to'].required = False


# =============================================================================
# SPARE PARTS FORMS
# =============================================================================

class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = [
            'name', 'description', 'category', 'quantity_on_hand',
            'reorder_level', 'reorder_quantity', 'unit_cost', 'currency',
            'status', 'location', 'vendor',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_on_hand': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
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


class SparePartUsageForm(forms.ModelForm):
    class Meta:
        model = SparePartUsage
        fields = ['asset', 'breakdown', 'quantity_used', 'used_date', 'notes']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'breakdown': forms.Select(attrs={'class': 'form-select'}),
            'quantity_used': forms.NumberInput(attrs={'class': 'form-control'}),
            'used_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.objects.filter(tenant=tenant)
            self.fields['breakdown'].queryset = BreakdownMaintenance.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['asset'].queryset = Asset.objects.none()
            self.fields['breakdown'].queryset = BreakdownMaintenance.objects.none()
        self.fields['asset'].required = False
        self.fields['breakdown'].required = False


SparePartUsageFormSet = forms.inlineformset_factory(
    SparePart,
    SparePartUsage,
    form=SparePartUsageForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# ASSET DEPRECIATION FORMS
# =============================================================================

class AssetDepreciationForm(forms.ModelForm):
    class Meta:
        model = AssetDepreciation
        fields = [
            'asset', 'method', 'original_cost', 'salvage_value',
            'useful_life_years', 'start_date', 'accumulated_depreciation',
            'current_book_value', 'currency', 'notes',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'original_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'salvage_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'useful_life_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'accumulated_depreciation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_book_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.objects.filter(tenant=tenant)
        else:
            self.fields['asset'].queryset = Asset.objects.none()
