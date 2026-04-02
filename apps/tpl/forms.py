from django import forms

from apps.inventory.models import Warehouse

from .models import (
    BillingInvoice,
    BillingInvoiceItem,
    BillingRate,
    Client,
    ClientInventoryItem,
    ClientStorageZone,
    IntegrationConfig,
    RentalAgreement,
    SLA,
    SLAMetric,
    SpaceUsageRecord,
)


# =============================================================================
# Client
# =============================================================================

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name', 'contact_person', 'email', 'phone',
            'address', 'city', 'country', 'default_currency',
            'contract_start_date', 'contract_end_date', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'default_currency': forms.Select(attrs={'class': 'form-select'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# Billing Rate
# =============================================================================

class BillingRateForm(forms.ModelForm):
    class Meta:
        model = BillingRate
        fields = [
            'client', 'rate_type', 'description', 'unit_of_measure',
            'rate_amount', 'currency', 'effective_date', 'end_date', 'is_active',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'rate_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., pallet/day, kg, order'}),
            'rate_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
        else:
            self.fields['client'].queryset = Client.objects.none()


# =============================================================================
# Billing Invoice
# =============================================================================

class BillingInvoiceForm(forms.ModelForm):
    class Meta:
        model = BillingInvoice
        fields = [
            'client', 'billing_period_start', 'billing_period_end',
            'subtotal', 'tax_amount', 'total_amount', 'currency',
            'due_date', 'issued_date', 'notes',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'billing_period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'billing_period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'issued_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
        else:
            self.fields['client'].queryset = Client.objects.none()


class BillingInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = BillingInvoiceItem
        fields = ['description', 'rate', 'quantity', 'unit_price', 'total_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


BillingInvoiceItemFormSet = forms.inlineformset_factory(
    BillingInvoice,
    BillingInvoiceItem,
    form=BillingInvoiceItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# Client Storage Zone
# =============================================================================

class ClientStorageZoneForm(forms.ModelForm):
    class Meta:
        model = ClientStorageZone
        fields = [
            'client', 'warehouse', 'zone_name', 'zone_type',
            'location_description', 'capacity', 'capacity_unit', 'is_active',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'zone_name': forms.TextInput(attrs={'class': 'form-control'}),
            'zone_type': forms.Select(attrs={'class': 'form-select'}),
            'location_description': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity_unit': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['client'].queryset = Client.objects.none()
            self.fields['warehouse'].queryset = Warehouse.objects.none()
        self.fields['warehouse'].required = False


# =============================================================================
# Client Inventory Item
# =============================================================================

class ClientInventoryItemForm(forms.ModelForm):
    class Meta:
        model = ClientInventoryItem
        fields = [
            'client', 'storage_zone', 'item_name', 'sku',
            'quantity', 'unit_of_measure', 'weight', 'weight_unit',
            'received_date', 'notes',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'storage_zone': forms.Select(attrs={'class': 'form-select'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'weight_unit': forms.Select(attrs={'class': 'form-select'}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
            self.fields['storage_zone'].queryset = ClientStorageZone.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['client'].queryset = Client.objects.none()
            self.fields['storage_zone'].queryset = ClientStorageZone.objects.none()
        self.fields['storage_zone'].required = False


# =============================================================================
# SLA
# =============================================================================

class SLAForm(forms.ModelForm):
    class Meta:
        model = SLA
        fields = [
            'client', 'title', 'effective_date', 'expiry_date',
            'review_frequency', 'description', 'penalty_clause',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'review_frequency': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'penalty_clause': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
        else:
            self.fields['client'].queryset = Client.objects.none()


class SLAMetricForm(forms.ModelForm):
    class Meta:
        model = SLAMetric
        fields = [
            'metric_name', 'metric_type', 'target_value', 'actual_value',
            'unit', 'measurement_period', 'is_breached', 'breach_notes',
        ]
        widgets = {
            'metric_name': forms.TextInput(attrs={'class': 'form-control'}),
            'metric_type': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., %, hours'}),
            'measurement_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., March 2026'}),
            'is_breached': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'breach_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


SLAMetricFormSet = forms.inlineformset_factory(
    SLA,
    SLAMetric,
    form=SLAMetricForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# Integration Config
# =============================================================================

class IntegrationConfigForm(forms.ModelForm):
    class Meta:
        model = IntegrationConfig
        fields = [
            'client', 'integration_name', 'api_key', 'api_endpoint',
            'webhook_url', 'sync_direction', 'sync_frequency', 'notes',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'integration_name': forms.TextInput(attrs={'class': 'form-control'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'api_endpoint': forms.URLInput(attrs={'class': 'form-control'}),
            'webhook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'sync_direction': forms.Select(attrs={'class': 'form-select'}),
            'sync_frequency': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
        else:
            self.fields['client'].queryset = Client.objects.none()


# =============================================================================
# Rental Agreement
# =============================================================================

class RentalAgreementForm(forms.ModelForm):
    class Meta:
        model = RentalAgreement
        fields = [
            'client', 'space_type', 'warehouse', 'area_size', 'area_unit',
            'rate_amount', 'rate_period', 'currency', 'start_date', 'end_date', 'terms',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'space_type': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'area_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'area_unit': forms.Select(attrs={'class': 'form-select'}),
            'rate_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rate_period': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(
                tenant=tenant, status='active',
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['client'].queryset = Client.objects.none()
            self.fields['warehouse'].queryset = Warehouse.objects.none()
        self.fields['warehouse'].required = False


class SpaceUsageRecordForm(forms.ModelForm):
    class Meta:
        model = SpaceUsageRecord
        fields = [
            'period_start', 'period_end', 'area_used',
            'utilization_percentage', 'calculated_charge', 'notes',
        ]
        widgets = {
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'area_used': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'utilization_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'calculated_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


SpaceUsageRecordFormSet = forms.inlineformset_factory(
    RentalAgreement,
    SpaceUsageRecord,
    form=SpaceUsageRecordForm,
    extra=1,
    can_delete=True,
)
