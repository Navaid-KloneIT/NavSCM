from django import forms

from apps.oms.models import Customer, Order
from apps.procurement.models import PurchaseOrder, Vendor
from apps.tms.models import Carrier, Shipment

from .models import (
    APInvoice,
    APInvoiceItem,
    APPayment,
    ARInvoice,
    ARInvoiceItem,
    ARPayment,
    Budget,
    BudgetEntry,
    LandedCostComponent,
    LandedCostSheet,
    TaxRate,
    TaxTransaction,
)


# =============================================================================
# Accounts Payable
# =============================================================================

class APInvoiceForm(forms.ModelForm):
    class Meta:
        model = APInvoice
        fields = [
            'vendor', 'purchase_order', 'invoice_date', 'due_date',
            'currency', 'subtotal', 'tax_amount', 'total_amount',
            'payment_terms', 'notes',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(tenant=tenant, is_active=True)
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(tenant=tenant)
        else:
            self.fields['vendor'].queryset = Vendor.objects.none()
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.none()
        self.fields['purchase_order'].required = False


class APInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = APInvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'total_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


APInvoiceItemFormSet = forms.inlineformset_factory(
    APInvoice, APInvoiceItem, form=APInvoiceItemForm, extra=1, can_delete=True,
)


class APPaymentForm(forms.ModelForm):
    class Meta:
        model = APPayment
        fields = ['invoice', 'payment_date', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['invoice'].queryset = APInvoice.objects.filter(
                tenant=tenant, status__in=['approved', 'partially_paid'],
            )
        else:
            self.fields['invoice'].queryset = APInvoice.objects.none()


# =============================================================================
# Accounts Receivable
# =============================================================================

class ARInvoiceForm(forms.ModelForm):
    class Meta:
        model = ARInvoice
        fields = [
            'customer', 'order', 'invoice_date', 'due_date',
            'currency', 'subtotal', 'tax_amount', 'total_amount', 'notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(tenant=tenant, is_active=True)
            self.fields['order'].queryset = Order.objects.filter(tenant=tenant)
        else:
            self.fields['customer'].queryset = Customer.objects.none()
            self.fields['order'].queryset = Order.objects.none()
        self.fields['order'].required = False


class ARInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = ARInvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'total_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


ARInvoiceItemFormSet = forms.inlineformset_factory(
    ARInvoice, ARInvoiceItem, form=ARInvoiceItemForm, extra=1, can_delete=True,
)


class ARPaymentForm(forms.ModelForm):
    class Meta:
        model = ARPayment
        fields = ['invoice', 'payment_date', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['invoice'].queryset = ARInvoice.objects.filter(
                tenant=tenant, status__in=['sent', 'partially_paid'],
            )
        else:
            self.fields['invoice'].queryset = ARInvoice.objects.none()


# =============================================================================
# Landed Cost
# =============================================================================

class LandedCostSheetForm(forms.ModelForm):
    class Meta:
        model = LandedCostSheet
        fields = [
            'shipment', 'purchase_order', 'carrier', 'currency',
            'total_goods_cost', 'total_landed_cost', 'notes',
        ]
        widgets = {
            'shipment': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'total_goods_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_landed_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['shipment'].queryset = Shipment.objects.filter(tenant=tenant)
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(tenant=tenant)
            self.fields['carrier'].queryset = Carrier.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['shipment'].queryset = Shipment.objects.none()
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.none()
            self.fields['carrier'].queryset = Carrier.objects.none()
        self.fields['shipment'].required = False
        self.fields['purchase_order'].required = False
        self.fields['carrier'].required = False


class LandedCostComponentForm(forms.ModelForm):
    class Meta:
        model = LandedCostComponent
        fields = ['cost_type', 'description', 'amount', 'allocation_method']
        widgets = {
            'cost_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'allocation_method': forms.Select(attrs={'class': 'form-select'}),
        }


LandedCostComponentFormSet = forms.inlineformset_factory(
    LandedCostSheet, LandedCostComponent, form=LandedCostComponentForm, extra=1, can_delete=True,
)


# =============================================================================
# Budgeting
# =============================================================================

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            'name', 'department', 'category', 'period_type',
            'period_start', 'period_end', 'currency', 'planned_amount', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'planned_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BudgetEntryForm(forms.ModelForm):
    class Meta:
        model = BudgetEntry
        fields = ['entry_date', 'description', 'amount', 'reference_type', 'reference_number']
        widgets = {
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reference_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., AP Invoice, PO'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., AP-00001'}),
        }


BudgetEntryFormSet = forms.inlineformset_factory(
    Budget, BudgetEntry, form=BudgetEntryForm, extra=1, can_delete=True,
)


# =============================================================================
# Tax Management
# =============================================================================

class TaxRateForm(forms.ModelForm):
    class Meta:
        model = TaxRate
        fields = [
            'name', 'tax_type', 'rate', 'country', 'region',
            'description', 'is_active', 'effective_from', 'effective_to',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TaxTransactionForm(forms.ModelForm):
    class Meta:
        model = TaxTransaction
        fields = [
            'tax_rate', 'transaction_type', 'taxable_amount', 'tax_amount',
            'transaction_date', 'reference_type', 'reference_number', 'notes',
        ]
        widgets = {
            'tax_rate': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'taxable_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., AP Invoice, AR Invoice'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., AP-00001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['tax_rate'].queryset = TaxRate.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['tax_rate'].queryset = TaxRate.objects.none()
        self.fields['tax_rate'].required = False
