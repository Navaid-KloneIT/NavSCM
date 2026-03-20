from django import forms

from .models import (
    GoodsReceiptNote,
    GRNItem,
    Item,
    ItemCategory,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RFQ,
    RFQItem,
    Vendor,
    VendorInvoice,
    VendorInvoiceItem,
)


# =============================================================================
# FOUNDATION FORMS
# =============================================================================

class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'code', 'description', 'category', 'unit_of_measure', 'unit_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = ItemCategory.objects.filter(
                tenant=tenant, is_active=True
            )


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'name', 'code', 'contact_person', 'email', 'phone',
            'address', 'city', 'country', 'tax_id', 'payment_terms', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================================
# PURCHASE REQUISITION FORMS
# =============================================================================

class PurchaseRequisitionForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisition
        fields = ['title', 'description', 'department', 'priority', 'required_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'required_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PurchaseRequisitionItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisitionItem
        fields = ['item', 'description', 'quantity', 'estimated_unit_price', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'estimated_unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        self.fields['item'].required = False


PurchaseRequisitionItemFormSet = forms.inlineformset_factory(
    PurchaseRequisition,
    PurchaseRequisitionItem,
    form=PurchaseRequisitionItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# RFQ FORMS
# =============================================================================

class RFQForm(forms.ModelForm):
    vendors = forms.ModelMultipleChoiceField(
        queryset=Vendor.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
    )

    class Meta:
        model = RFQ
        fields = ['title', 'description', 'requisition', 'submission_deadline', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requisition': forms.Select(attrs={'class': 'form-select'}),
            'submission_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendors'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['requisition'].queryset = PurchaseRequisition.objects.filter(
                tenant=tenant, status='approved'
            )
        self.fields['requisition'].required = False


class RFQItemForm(forms.ModelForm):
    class Meta:
        model = RFQItem
        fields = ['item', 'description', 'quantity', 'unit_of_measure']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        self.fields['item'].required = False


RFQItemFormSet = forms.inlineformset_factory(
    RFQ,
    RFQItem,
    form=RFQItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PURCHASE ORDER FORMS
# =============================================================================

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'vendor', 'rfq', 'requisition', 'order_date',
            'expected_delivery_date', 'tax_amount', 'discount_amount',
            'payment_terms', 'shipping_address', 'notes',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'rfq': forms.Select(attrs={'class': 'form-select'}),
            'requisition': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['rfq'].queryset = RFQ.objects.filter(tenant=tenant)
            self.fields['requisition'].queryset = PurchaseRequisition.objects.filter(
                tenant=tenant, status='approved'
            )
        self.fields['rfq'].required = False
        self.fields['requisition'].required = False


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'description', 'quantity', 'unit_price', 'tax_rate', 'discount']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        self.fields['item'].required = False


PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# GRN FORMS
# =============================================================================

class GoodsReceiptNoteForm(forms.ModelForm):
    class Meta:
        model = GoodsReceiptNote
        fields = ['purchase_order', 'received_date', 'notes']
        widgets = {
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                tenant=tenant,
                status__in=['approved', 'sent', 'acknowledged', 'partially_received'],
            )


class GRNItemForm(forms.ModelForm):
    class Meta:
        model = GRNItem
        fields = ['po_item', 'received_quantity', 'accepted_quantity', 'rejected_quantity', 'rejection_reason']
        widgets = {
            'po_item': forms.Select(attrs={'class': 'form-select'}),
            'received_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'accepted_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'rejected_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'rejection_reason': forms.TextInput(attrs={'class': 'form-control'}),
        }


GRNItemFormSet = forms.inlineformset_factory(
    GoodsReceiptNote,
    GRNItem,
    form=GRNItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# VENDOR INVOICE FORMS
# =============================================================================

class VendorInvoiceForm(forms.ModelForm):
    class Meta:
        model = VendorInvoice
        fields = [
            'invoice_number', 'vendor', 'purchase_order', 'grn',
            'invoice_date', 'due_date', 'subtotal', 'tax_amount', 'total_amount', 'notes',
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'grn': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                tenant=tenant
            )
            self.fields['grn'].queryset = GoodsReceiptNote.objects.filter(
                tenant=tenant
            )
        self.fields['purchase_order'].required = False
        self.fields['grn'].required = False


class VendorInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = VendorInvoiceItem
        fields = ['po_item', 'description', 'quantity', 'unit_price', 'total_price']
        widgets = {
            'po_item': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


VendorInvoiceItemFormSet = forms.inlineformset_factory(
    VendorInvoice,
    VendorInvoiceItem,
    form=VendorInvoiceItemForm,
    extra=1,
    can_delete=True,
)
