from django import forms
from django.contrib.auth import get_user_model

from apps.inventory.models import Warehouse
from apps.procurement.models import Item, Vendor
from apps.tms.models import Carrier

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

User = get_user_model()


# =============================================================================
# INVENTORY ANALYTICS FORMS
# =============================================================================

class InventoryAnalyticsForm(forms.ModelForm):
    class Meta:
        model = InventoryAnalytics
        fields = ['report_type', 'start_date', 'end_date', 'notes']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class InventoryAnalyticsItemForm(forms.ModelForm):
    class Meta:
        model = InventoryAnalyticsItem
        fields = [
            'item', 'warehouse', 'quantity_on_hand', 'quantity_reserved',
            'unit_cost', 'total_value', 'days_since_last_movement',
            'turnover_rate', 'is_dead_stock',
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'quantity_on_hand': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_reserved': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'days_since_last_movement': forms.NumberInput(attrs={'class': 'form-control'}),
            'turnover_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_dead_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['item'].queryset = Item.objects.none()
            self.fields['warehouse'].queryset = Warehouse.objects.none()


InventoryAnalyticsItemFormSet = forms.inlineformset_factory(
    InventoryAnalytics,
    InventoryAnalyticsItem,
    form=InventoryAnalyticsItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PROCUREMENT ANALYTICS FORMS
# =============================================================================

class ProcurementAnalyticsForm(forms.ModelForm):
    class Meta:
        model = ProcurementAnalytics
        fields = ['report_type', 'start_date', 'end_date', 'notes']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class ProcurementAnalyticsItemForm(forms.ModelForm):
    class Meta:
        model = ProcurementAnalyticsItem
        fields = [
            'vendor', 'total_spend', 'order_count', 'avg_lead_time_days',
            'on_time_rate', 'rejection_rate', 'cost_variance',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'total_spend': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'order_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'avg_lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'on_time_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rejection_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_variance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['vendor'].queryset = Vendor.objects.none()


ProcurementAnalyticsItemFormSet = forms.inlineformset_factory(
    ProcurementAnalytics,
    ProcurementAnalyticsItem,
    form=ProcurementAnalyticsItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# LOGISTICS KPI FORMS
# =============================================================================

class LogisticsKPIForm(forms.ModelForm):
    class Meta:
        model = LogisticsKPI
        fields = ['report_type', 'start_date', 'end_date', 'notes']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class LogisticsKPIItemForm(forms.ModelForm):
    class Meta:
        model = LogisticsKPIItem
        fields = [
            'carrier', 'shipment_count', 'on_time_count', 'late_count',
            'on_time_rate', 'total_cost', 'avg_cost_per_shipment', 'avg_transit_days',
        ]
        widgets = {
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'shipment_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'on_time_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'late_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'on_time_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'avg_cost_per_shipment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'avg_transit_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['carrier'].queryset = Carrier.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['carrier'].queryset = Carrier.objects.none()


LogisticsKPIItemFormSet = forms.inlineformset_factory(
    LogisticsKPI,
    LogisticsKPIItem,
    form=LogisticsKPIItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# FINANCIAL REPORT FORMS
# =============================================================================

class FinancialReportForm(forms.ModelForm):
    class Meta:
        model = FinancialReport
        fields = ['report_type', 'start_date', 'end_date', 'notes']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class FinancialReportItemForm(forms.ModelForm):
    class Meta:
        model = FinancialReportItem
        fields = ['category', 'description', 'amount', 'percentage_of_total']
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'percentage_of_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


FinancialReportItemFormSet = forms.inlineformset_factory(
    FinancialReport,
    FinancialReportItem,
    form=FinancialReportItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PREDICTIVE ALERT FORMS
# =============================================================================

class PredictiveAlertForm(forms.ModelForm):
    class Meta:
        model = PredictiveAlert
        fields = [
            'title', 'alert_type', 'severity', 'description',
            'affected_item', 'affected_vendor', 'predicted_date',
            'confidence_level', 'impact_description', 'recommended_action',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'alert_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'affected_item': forms.Select(attrs={'class': 'form-select'}),
            'affected_vendor': forms.Select(attrs={'class': 'form-select'}),
            'predicted_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'confidence_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'impact_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommended_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['affected_item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['affected_vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['affected_item'].queryset = Item.objects.none()
            self.fields['affected_vendor'].queryset = Vendor.objects.none()
        self.fields['affected_item'].required = False
        self.fields['affected_vendor'].required = False
