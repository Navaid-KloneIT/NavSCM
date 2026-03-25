from django import forms

from apps.procurement.models import Item

from .models import (
    Carrier,
    FreightBill,
    FreightBillItem,
    LoadPlan,
    LoadPlanItem,
    RateCard,
    Route,
    Shipment,
    ShipmentItem,
    ShipmentTracking,
)


# =============================================================================
# CARRIER MANAGEMENT
# =============================================================================

class CarrierForm(forms.ModelForm):
    class Meta:
        model = Carrier
        fields = [
            'name', 'contact_person', 'email', 'phone', 'address',
            'carrier_type', 'rating', 'is_active', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'carrier_type': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '5', 'step': '0.1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class RateCardForm(forms.ModelForm):
    class Meta:
        model = RateCard
        fields = [
            'carrier', 'origin', 'destination', 'transport_mode',
            'rate_per_unit', 'currency', 'unit_type', 'min_charge',
            'max_weight', 'transit_days', 'effective_from', 'effective_to',
            'is_active',
        ]
        widgets = {
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'transport_mode': forms.Select(attrs={'class': 'form-select'}),
            'rate_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'min_charge': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'max_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'transit_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['carrier'].queryset = Carrier.objects.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# ROUTE PLANNING
# =============================================================================

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = [
            'name', 'origin', 'destination', 'distance_km',
            'estimated_time_hours', 'carrier', 'transport_mode',
            'waypoints', 'fuel_cost_estimate', 'toll_cost_estimate', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'distance_km': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'estimated_time_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'transport_mode': forms.Select(attrs={'class': 'form-select'}),
            'waypoints': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comma-separated waypoints'}),
            'fuel_cost_estimate': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'toll_cost_estimate': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['carrier'].queryset = Carrier.objects.filter(
                tenant=tenant, is_active=True
            )
        self.fields['carrier'].required = False


# =============================================================================
# SHIPMENT TRACKING
# =============================================================================

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'order', 'carrier', 'route', 'origin_address', 'destination_address',
            'priority', 'transport_mode', 'estimated_departure', 'estimated_arrival',
            'total_weight', 'total_volume', 'tracking_url',
            'special_instructions', 'notes',
        ]
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'route': forms.Select(attrs={'class': 'form-select'}),
            'origin_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'destination_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'transport_mode': forms.Select(attrs={'class': 'form-select'}),
            'estimated_departure': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estimated_arrival': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'total_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'total_volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'tracking_url': forms.URLInput(attrs={'class': 'form-control'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.oms.models import Order
            self.fields['carrier'].queryset = Carrier.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['route'].queryset = Route.objects.filter(
                tenant=tenant, status='active'
            )
            self.fields['order'].queryset = Order.objects.filter(
                tenant=tenant
            ).exclude(status__in=['cancelled', 'draft'])
        self.fields['order'].required = False
        self.fields['route'].required = False
        self.fields['estimated_departure'].required = False
        self.fields['estimated_arrival'].required = False
        self.fields['tracking_url'].required = False


class ShipmentItemForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ['item', 'quantity', 'weight', 'volume', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)


ShipmentItemFormSet = forms.inlineformset_factory(
    Shipment,
    ShipmentItem,
    form=ShipmentItemForm,
    extra=1,
    can_delete=True,
)


class ShipmentTrackingForm(forms.ModelForm):
    class Meta:
        model = ShipmentTracking
        fields = ['location', 'status', 'notes', 'recorded_at']
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


# =============================================================================
# FREIGHT AUDIT & PAYMENT
# =============================================================================

class FreightBillForm(forms.ModelForm):
    class Meta:
        model = FreightBill
        fields = [
            'shipment', 'carrier', 'invoice_number', 'invoice_date',
            'due_date', 'amount', 'currency', 'notes',
        ]
        widgets = {
            'shipment': forms.Select(attrs={'class': 'form-select'}),
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['shipment'].queryset = Shipment.objects.filter(
                tenant=tenant
            )
            self.fields['carrier'].queryset = Carrier.objects.filter(
                tenant=tenant, is_active=True
            )


class FreightBillItemForm(forms.ModelForm):
    class Meta:
        model = FreightBillItem
        fields = ['description', 'quantity', 'unit_price', 'total_price', 'charge_type']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'charge_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


FreightBillItemFormSet = forms.inlineformset_factory(
    FreightBill,
    FreightBillItem,
    form=FreightBillItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# LOAD OPTIMIZATION
# =============================================================================

class LoadPlanForm(forms.ModelForm):
    class Meta:
        model = LoadPlan
        fields = [
            'shipment', 'vehicle_type', 'max_weight', 'max_volume',
            'planned_weight', 'planned_volume', 'notes',
        ]
        widgets = {
            'shipment': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'max_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'max_volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'planned_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'planned_volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['shipment'].queryset = Shipment.objects.filter(
                tenant=tenant
            )
        self.fields['shipment'].required = False


class LoadPlanItemForm(forms.ModelForm):
    class Meta:
        model = LoadPlanItem
        fields = ['item', 'quantity', 'weight', 'volume', 'load_sequence', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'load_sequence': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)


LoadPlanItemFormSet = forms.inlineformset_factory(
    LoadPlan,
    LoadPlanItem,
    form=LoadPlanItemForm,
    extra=1,
    can_delete=True,
)
