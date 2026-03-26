from django import forms

from apps.inventory.models import Warehouse
from apps.procurement.models import Item

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


# =============================================================================
# SALES FORECASTING FORMS
# =============================================================================

class SalesForecastForm(forms.ModelForm):
    class Meta:
        model = SalesForecast
        fields = [
            'title', 'description', 'forecast_method',
            'start_date', 'end_date', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'forecast_method': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class ForecastLineItemForm(forms.ModelForm):
    class Meta:
        model = ForecastLineItem
        fields = ['item', 'forecasted_quantity', 'actual_quantity', 'confidence_level', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'forecasted_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'confidence_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['item'].queryset = Item.objects.none()


ForecastLineItemFormSet = forms.inlineformset_factory(
    SalesForecast,
    ForecastLineItem,
    form=ForecastLineItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# SEASONALITY ANALYSIS FORMS
# =============================================================================

class SeasonalityProfileForm(forms.ModelForm):
    class Meta:
        model = SeasonalityProfile
        fields = [
            'item', 'name', 'description',
            'jan_factor', 'feb_factor', 'mar_factor', 'apr_factor',
            'may_factor', 'jun_factor', 'jul_factor', 'aug_factor',
            'sep_factor', 'oct_factor', 'nov_factor', 'dec_factor',
            'is_active',
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'jan_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'feb_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mar_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'apr_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'may_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'jun_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'jul_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aug_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sep_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'oct_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nov_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dec_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['item'].queryset = Item.objects.none()


class PromotionalEventForm(forms.ModelForm):
    class Meta:
        model = PromotionalEvent
        fields = [
            'name', 'description', 'event_type', 'seasonality_profile',
            'start_date', 'end_date', 'impact_factor', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'seasonality_profile': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'impact_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['seasonality_profile'].queryset = SeasonalityProfile.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['seasonality_profile'].queryset = SeasonalityProfile.objects.none()
        self.fields['seasonality_profile'].required = False


# =============================================================================
# DEMAND SENSING FORMS
# =============================================================================

class DemandSignalForm(forms.ModelForm):
    class Meta:
        model = DemandSignal
        fields = [
            'title', 'description', 'signal_type', 'impact_level',
            'item', 'estimated_impact_pct', 'signal_date', 'expiry_date',
            'source', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'signal_type': forms.Select(attrs={'class': 'form-select'}),
            'impact_level': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'estimated_impact_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'signal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['item'].queryset = Item.objects.none()
        self.fields['item'].required = False
        self.fields['expiry_date'].required = False


# =============================================================================
# COLLABORATIVE PLANNING FORMS
# =============================================================================

class CollaborativePlanForm(forms.ModelForm):
    class Meta:
        model = CollaborativePlan
        fields = [
            'title', 'description', 'plan_type',
            'start_date', 'end_date', 'forecast', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'plan_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'forecast': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['forecast'].queryset = SalesForecast.objects.filter(
                tenant=tenant,
            ).exclude(status='archived')
        else:
            self.fields['forecast'].queryset = SalesForecast.objects.none()
        self.fields['forecast'].required = False


class PlanLineItemForm(forms.ModelForm):
    class Meta:
        model = PlanLineItem
        fields = ['item', 'planned_quantity', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['item'].queryset = Item.objects.none()


PlanLineItemFormSet = forms.inlineformset_factory(
    CollaborativePlan,
    PlanLineItem,
    form=PlanLineItemForm,
    extra=1,
    can_delete=True,
)


class PlanCommentForm(forms.ModelForm):
    class Meta:
        model = PlanComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment...',
            }),
        }


# =============================================================================
# SAFETY STOCK FORMS
# =============================================================================

class SafetyStockCalculationForm(forms.ModelForm):
    class Meta:
        model = SafetyStockCalculation
        fields = [
            'title', 'description', 'calculation_method',
            'calculation_date', 'default_service_level', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'calculation_method': forms.Select(attrs={'class': 'form-select'}),
            'calculation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'default_service_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class SafetyStockItemForm(forms.ModelForm):
    class Meta:
        model = SafetyStockItem
        fields = [
            'item', 'warehouse', 'avg_demand', 'demand_std_dev',
            'lead_time_days', 'lead_time_std_dev', 'service_level_pct',
            'current_stock', 'notes',
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'avg_demand': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'demand_std_dev': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'lead_time_std_dev': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'service_level_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['item'].queryset = Item.objects.none()
            self.fields['warehouse'].queryset = Warehouse.objects.none()


SafetyStockItemFormSet = forms.inlineformset_factory(
    SafetyStockCalculation,
    SafetyStockItem,
    form=SafetyStockItemForm,
    extra=1,
    can_delete=True,
)
