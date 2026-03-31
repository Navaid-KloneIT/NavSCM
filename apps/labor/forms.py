from django import forms
from django.contrib.auth import get_user_model

from apps.inventory.models import Warehouse

from .models import (
    Attendance,
    LaborPlan,
    LaborPlanLine,
    PayrollRecord,
    PerformanceReview,
    TaskAssignment,
    TaskChecklistItem,
)

User = get_user_model()


# =============================================================================
# LABOR PLANNING FORMS
# =============================================================================

class LaborPlanForm(forms.ModelForm):
    class Meta:
        model = LaborPlan
        fields = [
            'title', 'warehouse', 'department', 'shift', 'plan_date',
            'expected_inbound_volume', 'expected_outbound_volume',
            'required_headcount', 'available_headcount', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'plan_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_inbound_volume': forms.NumberInput(attrs={'class': 'form-control'}),
            'expected_outbound_volume': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_headcount': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_headcount': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['warehouse'].queryset = Warehouse.objects.none()
        self.fields['warehouse'].required = False


class LaborPlanLineForm(forms.ModelForm):
    class Meta:
        model = LaborPlanLine
        fields = ['role', 'required_count', 'available_count', 'hourly_rate', 'notes']
        widgets = {
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'required_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


LaborPlanLineFormSet = forms.inlineformset_factory(
    LaborPlan,
    LaborPlanLine,
    form=LaborPlanLineForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# TIME & ATTENDANCE FORMS
# =============================================================================

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = [
            'worker', 'warehouse', 'date', 'shift', 'clock_in', 'clock_out',
            'break_start', 'break_end', 'break_duration_minutes',
            'overtime_hours', 'standard_hours_per_day', 'notes',
        ]
        widgets = {
            'worker': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'clock_in': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'clock_out': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'break_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'break_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'break_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'standard_hours_per_day': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['worker'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['worker'].queryset = User.objects.none()
            self.fields['warehouse'].queryset = Warehouse.objects.none()
        self.fields['warehouse'].required = False
        self.fields['clock_out'].required = False
        self.fields['break_start'].required = False
        self.fields['break_end'].required = False


# =============================================================================
# TASK ASSIGNMENT FORMS
# =============================================================================

class TaskAssignmentForm(forms.ModelForm):
    class Meta:
        model = TaskAssignment
        fields = [
            'title', 'task_type', 'priority', 'warehouse', 'assigned_to',
            'assigned_date', 'due_date', 'estimated_duration_minutes',
            'units_to_process', 'description', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'assigned_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'units_to_process': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['warehouse'].queryset = Warehouse.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['warehouse'].required = False
        self.fields['assigned_to'].required = False


class TaskChecklistItemForm(forms.ModelForm):
    class Meta:
        model = TaskChecklistItem
        fields = ['item_name', 'is_completed', 'notes']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


TaskChecklistItemFormSet = forms.inlineformset_factory(
    TaskAssignment,
    TaskChecklistItem,
    form=TaskChecklistItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PERFORMANCE TRACKING FORMS
# =============================================================================

class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = [
            'worker', 'warehouse', 'period_start', 'period_end',
            'tasks_completed', 'total_units_processed', 'total_hours_worked',
            'total_errors', 'rating', 'reviewed_by',
            'reviewer_comments', 'worker_comments',
        ]
        widgets = {
            'worker': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tasks_completed': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_units_processed': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_hours_worked': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_errors': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'reviewed_by': forms.Select(attrs={'class': 'form-select'}),
            'reviewer_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'worker_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['worker'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True,
            )
            self.fields['reviewed_by'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['worker'].queryset = User.objects.none()
            self.fields['warehouse'].queryset = Warehouse.objects.none()
            self.fields['reviewed_by'].queryset = User.objects.none()
        self.fields['warehouse'].required = False
        self.fields['reviewed_by'].required = False


# =============================================================================
# PAYROLL INTEGRATION FORMS
# =============================================================================

class PayrollRecordForm(forms.ModelForm):
    class Meta:
        model = PayrollRecord
        fields = [
            'worker', 'period_start', 'period_end', 'regular_hours',
            'overtime_hours', 'hourly_rate', 'overtime_rate',
            'deductions', 'bonuses', 'currency',
            'days_worked', 'days_absent', 'notes',
        ]
        widgets = {
            'worker': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'regular_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overtime_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bonuses': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'days_worked': forms.NumberInput(attrs={'class': 'form-control'}),
            'days_absent': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['worker'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['worker'].queryset = User.objects.none()
