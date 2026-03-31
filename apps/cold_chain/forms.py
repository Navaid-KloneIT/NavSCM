from django import forms
from django.contrib.auth import get_user_model

from .models import (
    ColdStorageItem,
    ColdStorageUnit,
    ComplianceReport,
    ComplianceReportItem,
    ReeferMaintenance,
    ReeferUnit,
    TemperatureExcursion,
    TemperatureReading,
    TemperatureSensor,
    TemperatureZone,
)

User = get_user_model()


# =============================================================================
# TEMPERATURE SENSOR FORMS
# =============================================================================

class TemperatureSensorForm(forms.ModelForm):
    class Meta:
        model = TemperatureSensor
        fields = [
            'name', 'sensor_type', 'location_type', 'manufacturer',
            'model_number', 'serial_number', 'installation_date',
            'last_calibration_date', 'next_calibration_date',
            'calibration_interval_days', 'location_description',
            'min_reading_range', 'max_reading_range',
            'reading_interval_minutes', 'description', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sensor_type': forms.Select(attrs={'class': 'form-select'}),
            'location_type': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_calibration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_calibration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'calibration_interval_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'location_description': forms.TextInput(attrs={'class': 'form-control'}),
            'min_reading_range': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_reading_range': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reading_interval_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TemperatureReadingForm(forms.ModelForm):
    class Meta:
        model = TemperatureReading
        fields = ['temperature', 'humidity', 'recorded_at', 'is_within_range', 'notes']
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_within_range': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


TemperatureReadingFormSet = forms.inlineformset_factory(
    TemperatureSensor,
    TemperatureReading,
    form=TemperatureReadingForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# TEMPERATURE ZONE FORMS
# =============================================================================

class TemperatureZoneForm(forms.ModelForm):
    class Meta:
        model = TemperatureZone
        fields = [
            'name', 'zone_type', 'min_temperature', 'max_temperature',
            'min_humidity', 'max_humidity', 'description', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'zone_type': forms.Select(attrs={'class': 'form-select'}),
            'min_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# TEMPERATURE EXCURSION FORMS
# =============================================================================

class TemperatureExcursionForm(forms.ModelForm):
    class Meta:
        model = TemperatureExcursion
        fields = [
            'sensor', 'zone', 'severity', 'detected_at',
            'temperature_recorded', 'expected_min', 'expected_max',
            'duration_minutes', 'affected_items_count',
            'impact_description', 'corrective_action', 'notes',
        ]
        widgets = {
            'sensor': forms.Select(attrs={'class': 'form-select'}),
            'zone': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'detected_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'temperature_recorded': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expected_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expected_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'affected_items_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'impact_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'corrective_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['sensor'].queryset = TemperatureSensor.objects.filter(
                tenant=tenant,
            )
            self.fields['zone'].queryset = TemperatureZone.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['sensor'].queryset = TemperatureSensor.objects.none()
            self.fields['zone'].queryset = TemperatureZone.objects.none()
        self.fields['sensor'].required = False
        self.fields['zone'].required = False


# =============================================================================
# COLD STORAGE UNIT FORMS
# =============================================================================

class ColdStorageUnitForm(forms.ModelForm):
    class Meta:
        model = ColdStorageUnit
        fields = [
            'name', 'unit_type', 'zone', 'capacity_cubic_meters',
            'current_temperature', 'current_humidity', 'location',
            'manufacturer', 'model_number', 'serial_number',
            'installation_date', 'description', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'zone': forms.Select(attrs={'class': 'form-select'}),
            'capacity_cubic_meters': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['zone'].queryset = TemperatureZone.objects.filter(
                tenant=tenant,
            )
        else:
            self.fields['zone'].queryset = TemperatureZone.objects.none()
        self.fields['zone'].required = False


class ColdStorageItemForm(forms.ModelForm):
    class Meta:
        model = ColdStorageItem
        fields = [
            'item_name', 'batch_number', 'lot_number', 'condition',
            'quantity', 'unit_of_measure', 'storage_date', 'expiry_date',
            'temperature_requirement_min', 'temperature_requirement_max',
            'notes',
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'storage_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'temperature_requirement_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'temperature_requirement_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


ColdStorageItemFormSet = forms.inlineformset_factory(
    ColdStorageUnit,
    ColdStorageItem,
    form=ColdStorageItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# COMPLIANCE REPORT FORMS
# =============================================================================

class ComplianceReportForm(forms.ModelForm):
    class Meta:
        model = ComplianceReport
        fields = [
            'title', 'report_type', 'period_start', 'period_end',
            'regulatory_body', 'findings_summary', 'recommendations',
            'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'regulatory_body': forms.Select(attrs={'class': 'form-select'}),
            'findings_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ComplianceReportItemForm(forms.ModelForm):
    class Meta:
        model = ComplianceReportItem
        fields = [
            'parameter_name', 'specification', 'measured_value',
            'unit_of_measure', 'result', 'notes',
        ]
        widgets = {
            'parameter_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specification': forms.TextInput(attrs={'class': 'form-control'}),
            'measured_value': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


ComplianceReportItemFormSet = forms.inlineformset_factory(
    ComplianceReport,
    ComplianceReportItem,
    form=ComplianceReportItemForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# REEFER UNIT FORMS
# =============================================================================

class ReeferUnitForm(forms.ModelForm):
    class Meta:
        model = ReeferUnit
        fields = [
            'name', 'unit_type', 'refrigerant_type', 'manufacturer',
            'model_number', 'serial_number', 'purchase_date',
            'purchase_cost', 'currency', 'last_service_date',
            'next_service_date', 'set_temperature', 'location',
            'description', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'refrigerant_type': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'last_service_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_service_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'set_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# REEFER MAINTENANCE FORMS
# =============================================================================

class ReeferMaintenanceForm(forms.ModelForm):
    class Meta:
        model = ReeferMaintenance
        fields = [
            'reefer', 'maintenance_type', 'priority', 'frequency',
            'title', 'description', 'scheduled_date', 'completed_date',
            'assigned_to', 'estimated_cost', 'actual_cost', 'currency',
            'findings', 'next_due_date', 'notes',
        ]
        widgets = {
            'reefer': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'completed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'findings': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['reefer'].queryset = ReeferUnit.objects.filter(
                tenant=tenant,
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                tenant=tenant, is_active=True,
            )
        else:
            self.fields['reefer'].queryset = ReeferUnit.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['assigned_to'].required = False
