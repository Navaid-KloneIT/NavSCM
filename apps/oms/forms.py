from django import forms

from apps.accounts.models import User
from apps.inventory.models import Warehouse
from apps.procurement.models import Item

from .models import (
    AllocationItem,
    Backorder,
    Customer,
    CustomerNotification,
    Order,
    OrderAllocation,
    OrderItem,
    OrderValidation,
    SalesChannel,
)


# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'company',
            'billing_address', 'shipping_address', 'credit_limit', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class SalesChannelForm(forms.ModelForm):
    class Meta:
        model = SalesChannel
        fields = ['name', 'channel_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'channel_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer', 'sales_channel', 'priority', 'order_date',
            'required_date', 'shipping_address', 'billing_address', 'notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'sales_channel': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'required_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['sales_channel'].queryset = SalesChannel.objects.filter(
                tenant=tenant, is_active=True
            )
        self.fields['sales_channel'].required = False
        self.fields['required_date'].required = False


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['item', 'quantity', 'unit_price', 'tax_amount', 'discount_amount']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)


OrderItemFormSet = forms.inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# ORDER ALLOCATION
# =============================================================================

class OrderAllocationForm(forms.ModelForm):
    class Meta:
        model = OrderAllocation
        fields = ['order', 'warehouse', 'allocation_method', 'notes']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'allocation_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['order'].queryset = Order.objects.filter(
                tenant=tenant, status='validated'
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class AllocationItemForm(forms.ModelForm):
    class Meta:
        model = AllocationItem
        fields = ['order_item', 'item', 'requested_quantity', 'allocated_quantity', 'warehouse']
        widgets = {
            'order_item': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'requested_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'allocated_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)


AllocationItemFormSet = forms.inlineformset_factory(
    OrderAllocation,
    AllocationItem,
    form=AllocationItemForm,
    extra=1,
    can_delete=True,
)
