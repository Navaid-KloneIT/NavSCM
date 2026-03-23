from django import forms

from apps.accounts.models import User
from apps.inventory.models import Warehouse
from apps.procurement.models import Item

from .models import (
    Bin,
    CycleCount,
    CycleCountItem,
    CycleCountPlan,
    DockAppointment,
    PackingOrder,
    PickList,
    PickListItem,
    PutAwayTask,
    ReceivingOrder,
    ReceivingOrderItem,
    ShippingLabel,
    YardLocation,
    YardVisit,
)


# =============================================================================
# BIN MANAGEMENT
# =============================================================================

class BinForm(forms.ModelForm):
    class Meta:
        model = Bin
        fields = [
            'warehouse', 'bin_code', 'zone', 'aisle', 'rack', 'shelf',
            'bin_position', 'bin_type', 'capacity', 'is_active',
        ]
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'bin_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if blank'}),
            'zone': forms.TextInput(attrs={'class': 'form-control'}),
            'aisle': forms.TextInput(attrs={'class': 'form-control'}),
            'rack': forms.TextInput(attrs={'class': 'form-control'}),
            'shelf': forms.TextInput(attrs={'class': 'form-control'}),
            'bin_position': forms.TextInput(attrs={'class': 'form-control'}),
            'bin_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bin_code'].required = False
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# INBOUND OPERATIONS
# =============================================================================

class DockAppointmentForm(forms.ModelForm):
    class Meta:
        model = DockAppointment
        fields = [
            'warehouse', 'dock_number', 'appointment_date', 'time_slot',
            'carrier_name', 'trailer_number', 'po_reference', 'notes',
        ]
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'dock_number': forms.TextInput(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'carrier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'trailer_number': forms.TextInput(attrs={'class': 'form-control'}),
            'po_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class ReceivingOrderForm(forms.ModelForm):
    class Meta:
        model = ReceivingOrder
        fields = ['warehouse', 'dock_appointment', 'po_reference', 'supplier_name', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'dock_appointment': forms.Select(attrs={'class': 'form-select'}),
            'po_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['dock_appointment'].queryset = DockAppointment.objects.filter(
                tenant=tenant
            ).exclude(status__in=['completed', 'cancelled'])
        self.fields['dock_appointment'].required = False


class ReceivingOrderItemForm(forms.ModelForm):
    class Meta:
        model = ReceivingOrderItem
        fields = ['item', 'expected_quantity', 'received_quantity', 'damaged_quantity', 'bin', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'expected_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'received_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'damaged_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'bin': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        self.fields['bin'].required = False


ReceivingOrderItemFormSet = forms.inlineformset_factory(
    ReceivingOrder,
    ReceivingOrderItem,
    form=ReceivingOrderItemForm,
    extra=1,
    can_delete=True,
)


class PutAwayTaskForm(forms.ModelForm):
    class Meta:
        model = PutAwayTask
        fields = ['receiving_order', 'item', 'quantity', 'source_bin', 'destination_bin', 'assigned_to']
        widgets = {
            'receiving_order': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'source_bin': forms.Select(attrs={'class': 'form-select'}),
            'destination_bin': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['receiving_order'].queryset = ReceivingOrder.objects.filter(tenant=tenant)
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['source_bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
            self.fields['destination_bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
            self.fields['assigned_to'].queryset = User.objects.filter(tenant=tenant, is_active=True)
        self.fields['source_bin'].required = False
        self.fields['destination_bin'].required = False
        self.fields['assigned_to'].required = False


# =============================================================================
# OUTBOUND OPERATIONS
# =============================================================================

class PickListForm(forms.ModelForm):
    class Meta:
        model = PickList
        fields = ['warehouse', 'pick_type', 'priority', 'assigned_to', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'pick_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True
            )
        self.fields['assigned_to'].required = False


class PickListItemForm(forms.ModelForm):
    class Meta:
        model = PickListItem
        fields = ['item', 'quantity_requested', 'quantity_picked', 'source_bin', 'status']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'quantity_picked': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'source_bin': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['source_bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        self.fields['source_bin'].required = False


PickListItemFormSet = forms.inlineformset_factory(
    PickList,
    PickListItem,
    form=PickListItemForm,
    extra=1,
    can_delete=True,
)


class PackingOrderForm(forms.ModelForm):
    class Meta:
        model = PackingOrder
        fields = ['warehouse', 'pick_list', 'shipping_method', 'total_weight', 'total_packages', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'pick_list': forms.Select(attrs={'class': 'form-select'}),
            'shipping_method': forms.TextInput(attrs={'class': 'form-control'}),
            'total_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'total_packages': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['pick_list'].queryset = PickList.objects.filter(
                tenant=tenant, status='completed'
            )
        self.fields['pick_list'].required = False


class ShippingLabelForm(forms.ModelForm):
    class Meta:
        model = ShippingLabel
        fields = ['carrier', 'tracking_number', 'destination_address', 'weight', 'dimensions']
        widgets = {
            'carrier': forms.TextInput(attrs={'class': 'form-control'}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L x W x H'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


# =============================================================================
# CYCLE COUNTING
# =============================================================================

class CycleCountPlanForm(forms.ModelForm):
    class Meta:
        model = CycleCountPlan
        fields = ['warehouse', 'name', 'count_type', 'frequency', 'start_date', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'count_type': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class CycleCountForm(forms.ModelForm):
    class Meta:
        model = CycleCount
        fields = ['warehouse', 'plan', 'counter', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'counter': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['plan'].queryset = CycleCountPlan.objects.filter(
                tenant=tenant, status='active'
            )
            self.fields['counter'].queryset = User.objects.filter(
                tenant=tenant, is_active=True
            )
        self.fields['plan'].required = False
        self.fields['counter'].required = False


class CycleCountItemForm(forms.ModelForm):
    class Meta:
        model = CycleCountItem
        fields = ['bin', 'item', 'expected_quantity', 'counted_quantity', 'notes']
        widgets = {
            'bin': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'expected_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'counted_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        self.fields['bin'].required = False


CycleCountItemFormSet = forms.inlineformset_factory(
    CycleCount,
    CycleCountItem,
    form=CycleCountItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# YARD MANAGEMENT
# =============================================================================

class YardLocationForm(forms.ModelForm):
    class Meta:
        model = YardLocation
        fields = ['warehouse', 'location_type', 'is_active', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'location_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class YardVisitForm(forms.ModelForm):
    class Meta:
        model = YardVisit
        fields = [
            'warehouse', 'yard_location', 'carrier_name', 'driver_name',
            'trailer_number', 'truck_number', 'visit_type', 'appointment', 'notes',
        ]
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'yard_location': forms.Select(attrs={'class': 'form-select'}),
            'carrier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'trailer_number': forms.TextInput(attrs={'class': 'form-control'}),
            'truck_number': forms.TextInput(attrs={'class': 'form-control'}),
            'visit_type': forms.Select(attrs={'class': 'form-select'}),
            'appointment': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['yard_location'].queryset = YardLocation.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['appointment'].queryset = DockAppointment.objects.filter(
                tenant=tenant
            ).exclude(status__in=['completed', 'cancelled'])
        self.fields['yard_location'].required = False
        self.fields['appointment'].required = False
