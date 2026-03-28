from django import forms
from django.contrib.auth import get_user_model

from apps.oms.models import Customer, Order
from apps.procurement.models import Item, Vendor

from .models import (
    Disposition,
    Refund,
    ReturnAuthorization,
    ReturnPortalSettings,
    RMALineItem,
    WarrantyClaim,
    WarrantyClaimItem,
)

User = get_user_model()


# =============================================================================
# RETURN AUTHORIZATION FORMS
# =============================================================================

class ReturnAuthorizationForm(forms.ModelForm):
    class Meta:
        model = ReturnAuthorization
        fields = [
            'customer', 'order', 'return_type', 'reason_category',
            'priority', 'requested_date', 'notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'return_type': forms.Select(attrs={'class': 'form-select'}),
            'reason_category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'requested_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['order'].queryset = Order.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['customer'].queryset = Customer.objects.none()
            self.fields['order'].queryset = Order.objects.none()
        self.fields['order'].required = False


class RMALineItemForm(forms.ModelForm):
    class Meta:
        model = RMALineItem
        fields = ['item', 'quantity', 'reason', 'condition']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['item'].queryset = Item.objects.none()


RMALineItemFormSet = forms.inlineformset_factory(
    ReturnAuthorization,
    RMALineItem,
    form=RMALineItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# REFUND FORMS
# =============================================================================

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = [
            'rma', 'refund_type', 'refund_method', 'amount',
            'currency', 'transaction_reference', 'notes',
        ]
        widgets = {
            'rma': forms.Select(attrs={'class': 'form-select'}),
            'refund_type': forms.Select(attrs={'class': 'form-select'}),
            'refund_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'transaction_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['rma'].queryset = ReturnAuthorization.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['rma'].queryset = ReturnAuthorization.objects.none()


# =============================================================================
# DISPOSITION FORMS
# =============================================================================

class DispositionForm(forms.ModelForm):
    class Meta:
        model = Disposition
        fields = [
            'rma', 'rma_item', 'item', 'quantity', 'condition_received',
            'disposition_decision', 'assigned_to', 'inspection_notes',
            'decision_notes',
        ]
        widgets = {
            'rma': forms.Select(attrs={'class': 'form-select'}),
            'rma_item': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'condition_received': forms.Select(attrs={'class': 'form-select'}),
            'disposition_decision': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'inspection_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'decision_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['rma'].queryset = ReturnAuthorization.objects.filter(
                tenant=tenant,
            )
            self.fields['rma_item'].queryset = RMALineItem.objects.filter(
                rma__tenant=tenant,
            )
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['rma'].queryset = ReturnAuthorization.objects.none()
            self.fields['rma_item'].queryset = RMALineItem.objects.none()
            self.fields['item'].queryset = Item.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['rma_item'].required = False
        self.fields['assigned_to'].required = False
        self.fields['disposition_decision'].required = False


# =============================================================================
# WARRANTY CLAIM FORMS
# =============================================================================

class WarrantyClaimForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = [
            'rma', 'vendor', 'item', 'claim_type', 'warranty_start_date',
            'warranty_end_date', 'claim_amount', 'settlement_amount',
            'currency', 'description', 'resolution_notes',
        ]
        widgets = {
            'rma': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'claim_type': forms.Select(attrs={'class': 'form-select'}),
            'warranty_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'claim_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'settlement_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['rma'].queryset = ReturnAuthorization.objects.filter(
                tenant=tenant,
            )
            self.fields['vendor'].queryset = Vendor.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['rma'].queryset = ReturnAuthorization.objects.none()
            self.fields['vendor'].queryset = Vendor.objects.none()
            self.fields['item'].queryset = Item.objects.none()
        self.fields['rma'].required = False


class WarrantyClaimItemForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaimItem
        fields = ['description', 'quantity', 'unit_cost', 'total']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


WarrantyClaimItemFormSet = forms.inlineformset_factory(
    WarrantyClaim,
    WarrantyClaimItem,
    form=WarrantyClaimItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# RETURN PORTAL SETTINGS FORM
# =============================================================================

class ReturnPortalSettingsForm(forms.ModelForm):
    class Meta:
        model = ReturnPortalSettings
        fields = [
            'is_portal_enabled', 'return_window_days', 'requires_approval',
            'auto_generate_labels', 'restocking_fee_percentage',
            'return_policy_text',
        ]
        widgets = {
            'is_portal_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'return_window_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_generate_labels': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'restocking_fee_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'return_policy_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
