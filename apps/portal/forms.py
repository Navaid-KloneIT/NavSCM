from django import forms
from django.contrib.auth import get_user_model

from apps.oms.models import Customer, Order
from apps.procurement.models import Item
from apps.tms.models import Shipment

from .models import (
    CatalogItem,
    OrderTracking,
    PortalAccount,
    PortalDocument,
    SupportTicket,
    TicketMessage,
    TrackingEvent,
)

User = get_user_model()


# =============================================================================
# PORTAL ACCOUNT FORMS
# =============================================================================

class PortalAccountForm(forms.ModelForm):
    class Meta:
        model = PortalAccount
        fields = [
            'customer', 'display_name', 'portal_email', 'phone',
            'preferred_language', 'billing_address', 'shipping_address',
            'payment_method', 'payment_reference', 'notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'portal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['customer'].queryset = Customer.objects.none()


# =============================================================================
# ORDER TRACKING FORMS
# =============================================================================

class OrderTrackingForm(forms.ModelForm):
    class Meta:
        model = OrderTracking
        fields = [
            'portal_account', 'order', 'shipment', 'estimated_delivery',
            'last_location', 'carrier_name', 'carrier_tracking_url', 'notes',
        ]
        widgets = {
            'portal_account': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'shipment': forms.Select(attrs={'class': 'form-select'}),
            'estimated_delivery': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_location': forms.TextInput(attrs={'class': 'form-control'}),
            'carrier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'carrier_tracking_url': forms.URLInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['portal_account'].queryset = PortalAccount.objects.filter(
                tenant=tenant,
            ).exclude(status='closed')
            self.fields['order'].queryset = Order.objects.filter(tenant=tenant)
            self.fields['shipment'].queryset = Shipment.objects.filter(tenant=tenant)
        else:
            self.fields['portal_account'].queryset = PortalAccount.objects.none()
            self.fields['order'].queryset = Order.objects.none()
            self.fields['shipment'].queryset = Shipment.objects.none()
        self.fields['shipment'].required = False


class TrackingEventForm(forms.ModelForm):
    class Meta:
        model = TrackingEvent
        fields = ['event_date', 'location', 'status', 'description']
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }


TrackingEventFormSet = forms.inlineformset_factory(
    OrderTracking,
    TrackingEvent,
    form=TrackingEventForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PORTAL DOCUMENT FORMS
# =============================================================================

class PortalDocumentForm(forms.ModelForm):
    class Meta:
        model = PortalDocument
        fields = [
            'portal_account', 'document_type', 'title', 'reference_number',
            'order', 'file_path', 'file_size', 'issue_date', 'expiry_date',
            'notes',
        ]
        widgets = {
            'portal_account': forms.Select(attrs={'class': 'form-select'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'file_path': forms.TextInput(attrs={'class': 'form-control'}),
            'file_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['portal_account'].queryset = PortalAccount.objects.filter(
                tenant=tenant,
            ).exclude(status='closed')
            self.fields['order'].queryset = Order.objects.filter(tenant=tenant)
        else:
            self.fields['portal_account'].queryset = PortalAccount.objects.none()
            self.fields['order'].queryset = Order.objects.none()
        self.fields['order'].required = False


# =============================================================================
# SUPPORT TICKET FORMS
# =============================================================================

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = [
            'portal_account', 'order', 'subject', 'category', 'priority',
            'description', 'assigned_to', 'resolution_notes',
        ]
        widgets = {
            'portal_account': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['portal_account'].queryset = PortalAccount.objects.filter(
                tenant=tenant,
            ).exclude(status='closed')
            self.fields['order'].queryset = Order.objects.filter(tenant=tenant)
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['portal_account'].queryset = PortalAccount.objects.none()
            self.fields['order'].queryset = Order.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['order'].required = False
        self.fields['assigned_to'].required = False


class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['sender_name', 'sender_type', 'message']
        widgets = {
            'sender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_type': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


TicketMessageFormSet = forms.inlineformset_factory(
    SupportTicket,
    TicketMessage,
    form=TicketMessageForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# CATALOG ITEM FORMS
# =============================================================================

class CatalogItemForm(forms.ModelForm):
    class Meta:
        model = CatalogItem
        fields = [
            'item', 'portal_name', 'portal_description', 'category',
            'unit_price', 'currency', 'stock_status', 'available_quantity',
            'minimum_order_quantity', 'lead_time_days', 'image_url',
            'is_featured', 'is_active',
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'portal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'portal_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'stock_status': forms.Select(attrs={'class': 'form-select'}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_order_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['item'].queryset = Item.objects.none()
