from django import forms

from apps.procurement.models import Item

from .models import (
    InventoryValuation,
    ReorderRule,
    StockAdjustment,
    StockAdjustmentItem,
    Warehouse,
    WarehouseLocation,
    WarehouseTransfer,
    WarehouseTransferItem,
)


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'code', 'warehouse_type', 'address', 'city', 'country', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if blank'}),
            'warehouse_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False


class WarehouseLocationForm(forms.ModelForm):
    class Meta:
        model = WarehouseLocation
        fields = ['name', 'code', 'zone', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'zone': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class WarehouseTransferForm(forms.ModelForm):
    class Meta:
        model = WarehouseTransfer
        fields = ['source_warehouse', 'destination_warehouse', 'transfer_date', 'notes']
        widgets = {
            'source_warehouse': forms.Select(attrs={'class': 'form-select'}),
            'destination_warehouse': forms.Select(attrs={'class': 'form-select'}),
            'transfer_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            active_warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
            self.fields['source_warehouse'].queryset = active_warehouses
            self.fields['destination_warehouse'].queryset = active_warehouses

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_warehouse')
        destination = cleaned_data.get('destination_warehouse')
        if source and destination and source == destination:
            raise forms.ValidationError('Source and destination warehouses must be different.')
        return cleaned_data


class WarehouseTransferItemForm(forms.ModelForm):
    class Meta:
        model = WarehouseTransferItem
        fields = ['item', 'quantity_requested', 'quantity_sent', 'quantity_received', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'quantity_sent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)


WarehouseTransferItemFormSet = forms.inlineformset_factory(
    WarehouseTransfer,
    WarehouseTransferItem,
    form=WarehouseTransferItemForm,
    extra=1,
    can_delete=True,
)


class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ['warehouse', 'adjustment_type', 'adjustment_date', 'reason', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class StockAdjustmentItemForm(forms.ModelForm):
    class Meta:
        model = StockAdjustmentItem
        fields = ['item', 'quantity_before', 'quantity_adjustment', 'quantity_after', 'unit_cost', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_before': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_adjustment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_after': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)


StockAdjustmentItemFormSet = forms.inlineformset_factory(
    StockAdjustment,
    StockAdjustmentItem,
    form=StockAdjustmentItemForm,
    extra=1,
    can_delete=True,
)


class ReorderRuleForm(forms.ModelForm):
    class Meta:
        model = ReorderRule
        fields = ['item', 'warehouse', 'reorder_point', 'reorder_quantity', 'safety_stock', 'lead_time_days', 'is_active']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'reorder_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class InventoryValuationForm(forms.ModelForm):
    class Meta:
        model = InventoryValuation
        fields = ['warehouse', 'valuation_method', 'valuation_date', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'valuation_method': forms.Select(attrs={'class': 'form-select'}),
            'valuation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )
        self.fields['warehouse'].required = False
