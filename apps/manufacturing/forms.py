from django import forms

from apps.inventory.models import Warehouse
from apps.procurement.models import Item

from .models import (
    BillOfMaterials,
    BOMLineItem,
    MRPRun,
    ProductionLog,
    ProductionSchedule,
    ProductionScheduleItem,
    WorkCenter,
    WorkOrder,
    WorkOrderOperation,
)


# =============================================================================
# WORK CENTER FORMS
# =============================================================================

class WorkCenterForm(forms.ModelForm):
    class Meta:
        model = WorkCenter
        fields = [
            'name', 'code', 'work_center_type', 'hourly_capacity',
            'cost_per_hour', 'is_active', 'location', 'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'work_center_type': forms.Select(attrs={'class': 'form-select'}),
            'hourly_capacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


# =============================================================================
# BILL OF MATERIALS FORMS
# =============================================================================

class BillOfMaterialsForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['product', 'version', 'title', 'yield_quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'yield_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['product'].queryset = Item.objects.none()


class BOMLineItemForm(forms.ModelForm):
    class Meta:
        model = BOMLineItem
        fields = ['item', 'quantity', 'unit_of_measure', 'scrap_percentage', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
            'scrap_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['item'].queryset = Item.objects.none()


BOMLineItemFormSet = forms.inlineformset_factory(
    BillOfMaterials,
    BOMLineItem,
    form=BOMLineItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PRODUCTION SCHEDULE FORMS
# =============================================================================

class ProductionScheduleForm(forms.ModelForm):
    class Meta:
        model = ProductionSchedule
        fields = ['title', 'start_date', 'end_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


class ProductionScheduleItemForm(forms.ModelForm):
    class Meta:
        model = ProductionScheduleItem
        fields = [
            'product', 'bom', 'planned_quantity', 'work_center',
            'planned_start', 'planned_end', 'priority', 'notes',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'bom': forms.Select(attrs={'class': 'form-select'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'work_center': forms.Select(attrs={'class': 'form-select'}),
            'planned_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['bom'].queryset = BillOfMaterials.objects.filter(tenant=tenant, status='active')
            self.fields['work_center'].queryset = WorkCenter.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['product'].queryset = Item.objects.none()
            self.fields['bom'].queryset = BillOfMaterials.objects.none()
            self.fields['work_center'].queryset = WorkCenter.objects.none()
        self.fields['bom'].required = False
        self.fields['work_center'].required = False


ProductionScheduleItemFormSet = forms.inlineformset_factory(
    ProductionSchedule,
    ProductionScheduleItem,
    form=ProductionScheduleItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# WORK ORDER FORMS
# =============================================================================

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'product', 'bom', 'schedule', 'work_center',
            'planned_quantity', 'planned_start_date', 'planned_end_date',
            'priority', 'notes',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'bom': forms.Select(attrs={'class': 'form-select'}),
            'schedule': forms.Select(attrs={'class': 'form-select'}),
            'work_center': forms.Select(attrs={'class': 'form-select'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'planned_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
            self.fields['bom'].queryset = BillOfMaterials.objects.filter(tenant=tenant, status='active')
            self.fields['schedule'].queryset = ProductionSchedule.objects.filter(
                tenant=tenant,
            ).exclude(status__in=['completed', 'cancelled'])
            self.fields['work_center'].queryset = WorkCenter.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['product'].queryset = Item.objects.none()
            self.fields['bom'].queryset = BillOfMaterials.objects.none()
            self.fields['schedule'].queryset = ProductionSchedule.objects.none()
            self.fields['work_center'].queryset = WorkCenter.objects.none()
        self.fields['bom'].required = False
        self.fields['schedule'].required = False
        self.fields['work_center'].required = False


class WorkOrderOperationForm(forms.ModelForm):
    class Meta:
        model = WorkOrderOperation
        fields = ['sequence', 'name', 'work_center', 'planned_duration_hours', 'notes']
        widgets = {
            'sequence': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'work_center': forms.Select(attrs={'class': 'form-select'}),
            'planned_duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['work_center'].queryset = WorkCenter.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['work_center'].queryset = WorkCenter.objects.none()
        self.fields['work_center'].required = False


WorkOrderOperationFormSet = forms.inlineformset_factory(
    WorkOrder,
    WorkOrderOperation,
    form=WorkOrderOperationForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# MRP FORMS
# =============================================================================

class MRPRunForm(forms.ModelForm):
    class Meta:
        model = MRPRun
        fields = ['title', 'run_date', 'planning_horizon_days', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'run_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planning_horizon_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


# =============================================================================
# PRODUCTION LOG FORMS
# =============================================================================

class ProductionLogForm(forms.ModelForm):
    class Meta:
        model = ProductionLog
        fields = [
            'work_order', 'operation', 'work_center', 'operator',
            'log_type', 'start_time', 'end_time',
            'quantity_produced', 'quantity_rejected', 'notes',
        ]
        widgets = {
            'work_order': forms.Select(attrs={'class': 'form-select'}),
            'operation': forms.Select(attrs={'class': 'form-select'}),
            'work_center': forms.Select(attrs={'class': 'form-select'}),
            'operator': forms.Select(attrs={'class': 'form-select'}),
            'log_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'quantity_produced': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_rejected': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['work_order'].queryset = WorkOrder.objects.filter(
                tenant=tenant,
            ).exclude(status__in=['completed', 'cancelled'])
            self.fields['operation'].queryset = WorkOrderOperation.objects.none()
            self.fields['work_center'].queryset = WorkCenter.objects.filter(tenant=tenant, is_active=True)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['operator'].queryset = User.objects.filter(tenant=tenant, is_active=True)
        else:
            self.fields['work_order'].queryset = WorkOrder.objects.none()
            self.fields['operation'].queryset = WorkOrderOperation.objects.none()
            self.fields['work_center'].queryset = WorkCenter.objects.none()
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['operator'].queryset = User.objects.none()
        self.fields['operation'].required = False
        self.fields['work_center'].required = False
        self.fields['operator'].required = False

        # If editing, populate operations from the selected work order
        if self.instance and self.instance.pk and self.instance.work_order:
            self.fields['operation'].queryset = self.instance.work_order.operations.all()
