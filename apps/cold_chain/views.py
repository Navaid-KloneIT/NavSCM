from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ColdStorageItemFormSet,
    ColdStorageUnitForm,
    ComplianceReportForm,
    ComplianceReportItemFormSet,
    ReeferMaintenanceForm,
    ReeferUnitForm,
    TemperatureExcursionForm,
    TemperatureReadingFormSet,
    TemperatureSensorForm,
    TemperatureZoneForm,
)
from .models import (
    ColdStorageUnit,
    ComplianceReport,
    ReeferMaintenance,
    ReeferUnit,
    TemperatureExcursion,
    TemperatureSensor,
    TemperatureZone,
)


# =============================================================================
# TEMPERATURE SENSOR VIEWS
# =============================================================================

@login_required
def sensor_list_view(request):
    tenant = request.tenant
    sensors = TemperatureSensor.objects.filter(tenant=tenant).select_related(
        'created_by',
    )
    status_choices = TemperatureSensor.STATUS_CHOICES
    type_choices = TemperatureSensor.SENSOR_TYPE_CHOICES
    location_choices = TemperatureSensor.LOCATION_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        sensors = sensors.filter(
            Q(sensor_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(serial_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        sensors = sensors.filter(status=status_filter)

    type_filter = request.GET.get('sensor_type', '').strip()
    if type_filter:
        sensors = sensors.filter(sensor_type=type_filter)

    location_filter = request.GET.get('location_type', '').strip()
    if location_filter:
        sensors = sensors.filter(location_type=location_filter)

    return render(request, 'cold_chain/sensor_list.html', {
        'sensors': sensors,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'location_choices': location_choices,
        'search_query': search_query,
    })


@login_required
def sensor_create_view(request):
    tenant = request.tenant
    form = TemperatureSensorForm(request.POST or None, tenant=tenant)
    formset = TemperatureReadingFormSet(request.POST or None, prefix='readings')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        sensor = form.save(commit=False)
        sensor.tenant = tenant
        sensor.created_by = request.user
        sensor.save()
        formset.instance = sensor
        formset.save()
        messages.success(request, f'Sensor {sensor.sensor_number} created successfully.')
        return redirect('cold_chain:sensor_detail', pk=sensor.pk)

    return render(request, 'cold_chain/sensor_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Temperature Sensor',
    })


@login_required
def sensor_detail_view(request, pk):
    sensor = get_object_or_404(TemperatureSensor, pk=pk, tenant=request.tenant)
    readings = sensor.readings.all()

    return render(request, 'cold_chain/sensor_detail.html', {
        'sensor': sensor,
        'readings': readings,
    })


@login_required
def sensor_edit_view(request, pk):
    tenant = request.tenant
    sensor = get_object_or_404(TemperatureSensor, pk=pk, tenant=tenant, status='draft')
    form = TemperatureSensorForm(request.POST or None, instance=sensor, tenant=tenant)
    formset = TemperatureReadingFormSet(
        request.POST or None, instance=sensor, prefix='readings',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Sensor {sensor.sensor_number} updated successfully.')
        return redirect('cold_chain:sensor_detail', pk=sensor.pk)

    return render(request, 'cold_chain/sensor_form.html', {
        'form': form,
        'formset': formset,
        'sensor': sensor,
        'title': 'Edit Temperature Sensor',
    })


@login_required
def sensor_delete_view(request, pk):
    sensor = get_object_or_404(
        TemperatureSensor, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        sensor.delete()
        messages.success(request, 'Temperature Sensor deleted successfully.')
        return redirect('cold_chain:sensor_list')
    return redirect('cold_chain:sensor_list')


@login_required
def sensor_activate_view(request, pk):
    sensor = get_object_or_404(
        TemperatureSensor, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        sensor.status = 'active'
        sensor.save()
        messages.success(request, f'Sensor {sensor.sensor_number} activated.')
    return redirect('cold_chain:sensor_detail', pk=sensor.pk)


@login_required
def sensor_offline_view(request, pk):
    sensor = get_object_or_404(
        TemperatureSensor, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        sensor.status = 'offline'
        sensor.save()
        messages.info(request, f'Sensor {sensor.sensor_number} set to offline.')
    return redirect('cold_chain:sensor_detail', pk=sensor.pk)


@login_required
def sensor_maintenance_view(request, pk):
    sensor = get_object_or_404(TemperatureSensor, pk=pk, tenant=request.tenant)
    if sensor.status not in ('active', 'offline'):
        return redirect('cold_chain:sensor_detail', pk=sensor.pk)
    if request.method == 'POST':
        sensor.status = 'maintenance'
        sensor.save()
        messages.info(request, f'Sensor {sensor.sensor_number} moved to maintenance.')
    return redirect('cold_chain:sensor_detail', pk=sensor.pk)


@login_required
def sensor_retire_view(request, pk):
    sensor = get_object_or_404(TemperatureSensor, pk=pk, tenant=request.tenant)
    if sensor.status in ('draft', 'retired'):
        return redirect('cold_chain:sensor_detail', pk=sensor.pk)
    if request.method == 'POST':
        sensor.status = 'retired'
        sensor.save()
        messages.warning(request, f'Sensor {sensor.sensor_number} retired.')
    return redirect('cold_chain:sensor_detail', pk=sensor.pk)


# =============================================================================
# TEMPERATURE ZONE VIEWS
# =============================================================================

@login_required
def zone_list_view(request):
    tenant = request.tenant
    zones = TemperatureZone.objects.filter(tenant=tenant)
    status_choices = TemperatureZone.STATUS_CHOICES
    type_choices = TemperatureZone.ZONE_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        zones = zones.filter(
            Q(zone_number__icontains=search_query)
            | Q(name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        zones = zones.filter(status=status_filter)

    type_filter = request.GET.get('zone_type', '').strip()
    if type_filter:
        zones = zones.filter(zone_type=type_filter)

    return render(request, 'cold_chain/zone_list.html', {
        'zones': zones,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def zone_create_view(request):
    tenant = request.tenant
    form = TemperatureZoneForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        zone = form.save(commit=False)
        zone.tenant = tenant
        zone.created_by = request.user
        zone.save()
        messages.success(request, f'Zone {zone.zone_number} created successfully.')
        return redirect('cold_chain:zone_detail', pk=zone.pk)

    return render(request, 'cold_chain/zone_form.html', {
        'form': form,
        'title': 'New Temperature Zone',
    })


@login_required
def zone_detail_view(request, pk):
    zone = get_object_or_404(TemperatureZone, pk=pk, tenant=request.tenant)
    storage_units = zone.storage_units.all()

    return render(request, 'cold_chain/zone_detail.html', {
        'zone': zone,
        'storage_units': storage_units,
    })


@login_required
def zone_edit_view(request, pk):
    tenant = request.tenant
    zone = get_object_or_404(TemperatureZone, pk=pk, tenant=tenant, status='draft')
    form = TemperatureZoneForm(request.POST or None, instance=zone, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Zone {zone.zone_number} updated successfully.')
        return redirect('cold_chain:zone_detail', pk=zone.pk)

    return render(request, 'cold_chain/zone_form.html', {
        'form': form,
        'zone': zone,
        'title': 'Edit Temperature Zone',
    })


@login_required
def zone_delete_view(request, pk):
    zone = get_object_or_404(
        TemperatureZone, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        zone.delete()
        messages.success(request, 'Temperature Zone deleted successfully.')
        return redirect('cold_chain:zone_list')
    return redirect('cold_chain:zone_list')


@login_required
def zone_activate_view(request, pk):
    zone = get_object_or_404(
        TemperatureZone, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        zone.status = 'active'
        zone.save()
        messages.success(request, f'Zone {zone.zone_number} activated.')
    return redirect('cold_chain:zone_detail', pk=zone.pk)


@login_required
def zone_deactivate_view(request, pk):
    zone = get_object_or_404(
        TemperatureZone, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        zone.status = 'inactive'
        zone.save()
        messages.warning(request, f'Zone {zone.zone_number} deactivated.')
    return redirect('cold_chain:zone_detail', pk=zone.pk)


# =============================================================================
# TEMPERATURE EXCURSION VIEWS
# =============================================================================

@login_required
def excursion_list_view(request):
    tenant = request.tenant
    excursions = TemperatureExcursion.objects.filter(tenant=tenant).select_related(
        'sensor', 'zone',
    )
    status_choices = TemperatureExcursion.STATUS_CHOICES
    severity_choices = TemperatureExcursion.SEVERITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        excursions = excursions.filter(
            Q(excursion_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        excursions = excursions.filter(status=status_filter)

    severity_filter = request.GET.get('severity', '').strip()
    if severity_filter:
        excursions = excursions.filter(severity=severity_filter)

    return render(request, 'cold_chain/excursion_list.html', {
        'excursions': excursions,
        'status_choices': status_choices,
        'severity_choices': severity_choices,
        'search_query': search_query,
    })


@login_required
def excursion_create_view(request):
    tenant = request.tenant
    form = TemperatureExcursionForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        excursion = form.save(commit=False)
        excursion.tenant = tenant
        excursion.created_by = request.user
        excursion.save()
        messages.success(request, f'Excursion {excursion.excursion_number} created successfully.')
        return redirect('cold_chain:excursion_detail', pk=excursion.pk)

    return render(request, 'cold_chain/excursion_form.html', {
        'form': form,
        'title': 'New Temperature Excursion',
    })


@login_required
def excursion_detail_view(request, pk):
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=request.tenant,
    )

    return render(request, 'cold_chain/excursion_detail.html', {
        'excursion': excursion,
    })


@login_required
def excursion_edit_view(request, pk):
    tenant = request.tenant
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=tenant, status='detected',
    )
    form = TemperatureExcursionForm(
        request.POST or None, instance=excursion, tenant=tenant,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Excursion {excursion.excursion_number} updated successfully.')
        return redirect('cold_chain:excursion_detail', pk=excursion.pk)

    return render(request, 'cold_chain/excursion_form.html', {
        'form': form,
        'excursion': excursion,
        'title': 'Edit Temperature Excursion',
    })


@login_required
def excursion_delete_view(request, pk):
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=request.tenant, status='detected',
    )
    if request.method == 'POST':
        excursion.delete()
        messages.success(request, 'Temperature Excursion deleted successfully.')
        return redirect('cold_chain:excursion_list')
    return redirect('cold_chain:excursion_list')


@login_required
def excursion_acknowledge_view(request, pk):
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=request.tenant, status='detected',
    )
    if request.method == 'POST':
        excursion.status = 'acknowledged'
        excursion.acknowledged_at = timezone.now()
        excursion.save()
        messages.info(request, f'Excursion {excursion.excursion_number} acknowledged.')
    return redirect('cold_chain:excursion_detail', pk=excursion.pk)


@login_required
def excursion_investigate_view(request, pk):
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=request.tenant, status='acknowledged',
    )
    if request.method == 'POST':
        excursion.status = 'investigating'
        excursion.save()
        messages.info(request, f'Excursion {excursion.excursion_number} investigation started.')
    return redirect('cold_chain:excursion_detail', pk=excursion.pk)


@login_required
def excursion_resolve_view(request, pk):
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=request.tenant, status='investigating',
    )
    if request.method == 'POST':
        excursion.status = 'resolved'
        excursion.resolved_at = timezone.now()
        excursion.resolved_by = request.user
        excursion.save()
        messages.success(request, f'Excursion {excursion.excursion_number} resolved.')
    return redirect('cold_chain:excursion_detail', pk=excursion.pk)


@login_required
def excursion_close_view(request, pk):
    excursion = get_object_or_404(
        TemperatureExcursion, pk=pk, tenant=request.tenant, status='resolved',
    )
    if request.method == 'POST':
        excursion.status = 'closed'
        excursion.save()
        messages.warning(request, f'Excursion {excursion.excursion_number} closed.')
    return redirect('cold_chain:excursion_detail', pk=excursion.pk)


# =============================================================================
# COLD STORAGE UNIT VIEWS
# =============================================================================

@login_required
def storage_list_view(request):
    tenant = request.tenant
    units = ColdStorageUnit.objects.filter(tenant=tenant).select_related(
        'zone', 'created_by',
    )
    status_choices = ColdStorageUnit.STATUS_CHOICES
    type_choices = ColdStorageUnit.UNIT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        units = units.filter(
            Q(unit_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(serial_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        units = units.filter(status=status_filter)

    type_filter = request.GET.get('unit_type', '').strip()
    if type_filter:
        units = units.filter(unit_type=type_filter)

    return render(request, 'cold_chain/storage_list.html', {
        'units': units,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def storage_create_view(request):
    tenant = request.tenant
    form = ColdStorageUnitForm(request.POST or None, tenant=tenant)
    formset = ColdStorageItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        unit = form.save(commit=False)
        unit.tenant = tenant
        unit.created_by = request.user
        unit.save()
        formset.instance = unit
        formset.save()
        messages.success(request, f'Storage Unit {unit.unit_number} created successfully.')
        return redirect('cold_chain:storage_detail', pk=unit.pk)

    return render(request, 'cold_chain/storage_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Cold Storage Unit',
    })


@login_required
def storage_detail_view(request, pk):
    unit = get_object_or_404(ColdStorageUnit, pk=pk, tenant=request.tenant)
    items = unit.items.all()

    return render(request, 'cold_chain/storage_detail.html', {
        'unit': unit,
        'items': items,
    })


@login_required
def storage_edit_view(request, pk):
    tenant = request.tenant
    unit = get_object_or_404(ColdStorageUnit, pk=pk, tenant=tenant, status='draft')
    form = ColdStorageUnitForm(request.POST or None, instance=unit, tenant=tenant)
    formset = ColdStorageItemFormSet(
        request.POST or None, instance=unit, prefix='items',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Storage Unit {unit.unit_number} updated successfully.')
        return redirect('cold_chain:storage_detail', pk=unit.pk)

    return render(request, 'cold_chain/storage_form.html', {
        'form': form,
        'formset': formset,
        'unit': unit,
        'title': 'Edit Cold Storage Unit',
    })


@login_required
def storage_delete_view(request, pk):
    unit = get_object_or_404(
        ColdStorageUnit, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        unit.delete()
        messages.success(request, 'Cold Storage Unit deleted successfully.')
        return redirect('cold_chain:storage_list')
    return redirect('cold_chain:storage_list')


@login_required
def storage_activate_view(request, pk):
    unit = get_object_or_404(
        ColdStorageUnit, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        unit.status = 'active'
        unit.save()
        messages.success(request, f'Storage Unit {unit.unit_number} activated.')
    return redirect('cold_chain:storage_detail', pk=unit.pk)


@login_required
def storage_maintenance_view(request, pk):
    unit = get_object_or_404(
        ColdStorageUnit, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        unit.status = 'maintenance'
        unit.save()
        messages.info(request, f'Storage Unit {unit.unit_number} moved to maintenance.')
    return redirect('cold_chain:storage_detail', pk=unit.pk)


@login_required
def storage_restore_view(request, pk):
    unit = get_object_or_404(ColdStorageUnit, pk=pk, tenant=request.tenant)
    if unit.status not in ('maintenance', 'out_of_service'):
        return redirect('cold_chain:storage_detail', pk=unit.pk)
    if request.method == 'POST':
        unit.status = 'active'
        unit.save()
        messages.success(request, f'Storage Unit {unit.unit_number} restored to active.')
    return redirect('cold_chain:storage_detail', pk=unit.pk)


@login_required
def storage_retire_view(request, pk):
    unit = get_object_or_404(ColdStorageUnit, pk=pk, tenant=request.tenant)
    if unit.status == 'retired':
        return redirect('cold_chain:storage_detail', pk=unit.pk)
    if request.method == 'POST':
        unit.status = 'retired'
        unit.save()
        messages.warning(request, f'Storage Unit {unit.unit_number} retired.')
    return redirect('cold_chain:storage_detail', pk=unit.pk)


# =============================================================================
# COMPLIANCE REPORT VIEWS
# =============================================================================

@login_required
def compliance_list_view(request):
    tenant = request.tenant
    reports = ComplianceReport.objects.filter(tenant=tenant)
    status_choices = ComplianceReport.STATUS_CHOICES
    type_choices = ComplianceReport.REPORT_TYPE_CHOICES
    body_choices = ComplianceReport.REGULATORY_BODY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reports = reports.filter(
            Q(report_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reports = reports.filter(status=status_filter)

    type_filter = request.GET.get('report_type', '').strip()
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    body_filter = request.GET.get('regulatory_body', '').strip()
    if body_filter:
        reports = reports.filter(regulatory_body=body_filter)

    return render(request, 'cold_chain/compliance_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'body_choices': body_choices,
        'search_query': search_query,
    })


@login_required
def compliance_create_view(request):
    tenant = request.tenant
    form = ComplianceReportForm(request.POST or None, tenant=tenant)
    formset = ComplianceReportItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        report = form.save(commit=False)
        report.tenant = tenant
        report.created_by = request.user
        report.save()
        formset.instance = report
        formset.save()
        messages.success(request, f'Report {report.report_number} created successfully.')
        return redirect('cold_chain:compliance_detail', pk=report.pk)

    return render(request, 'cold_chain/compliance_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Compliance Report',
    })


@login_required
def compliance_detail_view(request, pk):
    report = get_object_or_404(ComplianceReport, pk=pk, tenant=request.tenant)
    items = report.items.all()

    return render(request, 'cold_chain/compliance_detail.html', {
        'report': report,
        'items': items,
    })


@login_required
def compliance_edit_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(
        ComplianceReport, pk=pk, tenant=tenant, status='draft',
    )
    form = ComplianceReportForm(request.POST or None, instance=report, tenant=tenant)
    formset = ComplianceReportItemFormSet(
        request.POST or None, instance=report, prefix='items',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Report {report.report_number} updated successfully.')
        return redirect('cold_chain:compliance_detail', pk=report.pk)

    return render(request, 'cold_chain/compliance_form.html', {
        'form': form,
        'formset': formset,
        'report': report,
        'title': 'Edit Compliance Report',
    })


@login_required
def compliance_delete_view(request, pk):
    report = get_object_or_404(
        ComplianceReport, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Compliance Report deleted successfully.')
        return redirect('cold_chain:compliance_list')
    return redirect('cold_chain:compliance_list')


@login_required
def compliance_generate_view(request, pk):
    report = get_object_or_404(
        ComplianceReport, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        report.status = 'generated'
        report.save()
        messages.info(request, f'Report {report.report_number} generated.')
    return redirect('cold_chain:compliance_detail', pk=report.pk)


@login_required
def compliance_review_view(request, pk):
    report = get_object_or_404(
        ComplianceReport, pk=pk, tenant=request.tenant, status='generated',
    )
    if request.method == 'POST':
        report.status = 'reviewed'
        report.save()
        messages.info(request, f'Report {report.report_number} reviewed.')
    return redirect('cold_chain:compliance_detail', pk=report.pk)


@login_required
def compliance_submit_view(request, pk):
    report = get_object_or_404(
        ComplianceReport, pk=pk, tenant=request.tenant, status='reviewed',
    )
    if request.method == 'POST':
        report.status = 'submitted'
        report.save()
        messages.info(request, f'Report {report.report_number} submitted.')
    return redirect('cold_chain:compliance_detail', pk=report.pk)


@login_required
def compliance_approve_view(request, pk):
    report = get_object_or_404(
        ComplianceReport, pk=pk, tenant=request.tenant, status='submitted',
    )
    if request.method == 'POST':
        report.status = 'approved'
        report.approved_by = request.user
        report.approved_at = timezone.now()
        report.save()
        messages.success(request, f'Report {report.report_number} approved.')
    return redirect('cold_chain:compliance_detail', pk=report.pk)


# =============================================================================
# REEFER UNIT VIEWS
# =============================================================================

@login_required
def reefer_list_view(request):
    tenant = request.tenant
    reefers = ReeferUnit.objects.filter(tenant=tenant)
    status_choices = ReeferUnit.STATUS_CHOICES
    type_choices = ReeferUnit.UNIT_TYPE_CHOICES
    refrigerant_choices = ReeferUnit.REFRIGERANT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reefers = reefers.filter(
            Q(unit_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(serial_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reefers = reefers.filter(status=status_filter)

    type_filter = request.GET.get('unit_type', '').strip()
    if type_filter:
        reefers = reefers.filter(unit_type=type_filter)

    refrigerant_filter = request.GET.get('refrigerant_type', '').strip()
    if refrigerant_filter:
        reefers = reefers.filter(refrigerant_type=refrigerant_filter)

    return render(request, 'cold_chain/reefer_list.html', {
        'reefers': reefers,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'refrigerant_choices': refrigerant_choices,
        'search_query': search_query,
    })


@login_required
def reefer_create_view(request):
    tenant = request.tenant
    form = ReeferUnitForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        reefer = form.save(commit=False)
        reefer.tenant = tenant
        reefer.created_by = request.user
        reefer.save()
        messages.success(request, f'Reefer Unit {reefer.unit_number} created successfully.')
        return redirect('cold_chain:reefer_detail', pk=reefer.pk)

    return render(request, 'cold_chain/reefer_form.html', {
        'form': form,
        'title': 'New Reefer Unit',
    })


@login_required
def reefer_detail_view(request, pk):
    reefer = get_object_or_404(ReeferUnit, pk=pk, tenant=request.tenant)
    maintenances = reefer.maintenances.all()

    return render(request, 'cold_chain/reefer_detail.html', {
        'reefer': reefer,
        'maintenances': maintenances,
    })


@login_required
def reefer_edit_view(request, pk):
    tenant = request.tenant
    reefer = get_object_or_404(ReeferUnit, pk=pk, tenant=tenant, status='draft')
    form = ReeferUnitForm(request.POST or None, instance=reefer, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Reefer Unit {reefer.unit_number} updated successfully.')
        return redirect('cold_chain:reefer_detail', pk=reefer.pk)

    return render(request, 'cold_chain/reefer_form.html', {
        'form': form,
        'reefer': reefer,
        'title': 'Edit Reefer Unit',
    })


@login_required
def reefer_delete_view(request, pk):
    reefer = get_object_or_404(
        ReeferUnit, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        reefer.delete()
        messages.success(request, 'Reefer Unit deleted successfully.')
        return redirect('cold_chain:reefer_list')
    return redirect('cold_chain:reefer_list')


@login_required
def reefer_activate_view(request, pk):
    reefer = get_object_or_404(
        ReeferUnit, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        reefer.status = 'active'
        reefer.save()
        messages.success(request, f'Reefer Unit {reefer.unit_number} activated.')
    return redirect('cold_chain:reefer_detail', pk=reefer.pk)


@login_required
def reefer_maintenance_status_view(request, pk):
    reefer = get_object_or_404(
        ReeferUnit, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        reefer.status = 'maintenance'
        reefer.save()
        messages.info(request, f'Reefer Unit {reefer.unit_number} moved to maintenance.')
    return redirect('cold_chain:reefer_detail', pk=reefer.pk)


@login_required
def reefer_restore_view(request, pk):
    reefer = get_object_or_404(ReeferUnit, pk=pk, tenant=request.tenant)
    if reefer.status not in ('maintenance', 'out_of_service'):
        return redirect('cold_chain:reefer_detail', pk=reefer.pk)
    if request.method == 'POST':
        reefer.status = 'active'
        reefer.save()
        messages.success(request, f'Reefer Unit {reefer.unit_number} restored to active.')
    return redirect('cold_chain:reefer_detail', pk=reefer.pk)


@login_required
def reefer_retire_view(request, pk):
    reefer = get_object_or_404(ReeferUnit, pk=pk, tenant=request.tenant)
    if reefer.status == 'retired':
        return redirect('cold_chain:reefer_detail', pk=reefer.pk)
    if request.method == 'POST':
        reefer.status = 'retired'
        reefer.save()
        messages.warning(request, f'Reefer Unit {reefer.unit_number} retired.')
    return redirect('cold_chain:reefer_detail', pk=reefer.pk)


# =============================================================================
# REEFER MAINTENANCE VIEWS
# =============================================================================

@login_required
def reefer_maint_list_view(request):
    tenant = request.tenant
    maintenances = ReeferMaintenance.objects.filter(tenant=tenant).select_related(
        'reefer', 'assigned_to',
    )
    status_choices = ReeferMaintenance.STATUS_CHOICES
    type_choices = ReeferMaintenance.MAINTENANCE_TYPE_CHOICES
    priority_choices = ReeferMaintenance.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        maintenances = maintenances.filter(
            Q(maintenance_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        maintenances = maintenances.filter(status=status_filter)

    type_filter = request.GET.get('maintenance_type', '').strip()
    if type_filter:
        maintenances = maintenances.filter(maintenance_type=type_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        maintenances = maintenances.filter(priority=priority_filter)

    return render(request, 'cold_chain/reefer_maint_list.html', {
        'maintenances': maintenances,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def reefer_maint_create_view(request):
    tenant = request.tenant
    form = ReeferMaintenanceForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        maint = form.save(commit=False)
        maint.tenant = tenant
        maint.created_by = request.user
        maint.save()
        messages.success(request, f'Maintenance {maint.maintenance_number} created successfully.')
        return redirect('cold_chain:reefer_maint_detail', pk=maint.pk)

    return render(request, 'cold_chain/reefer_maint_form.html', {
        'form': form,
        'title': 'New Reefer Maintenance',
    })


@login_required
def reefer_maint_detail_view(request, pk):
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=request.tenant,
    )

    return render(request, 'cold_chain/reefer_maint_detail.html', {
        'maintenance': maintenance,
    })


@login_required
def reefer_maint_edit_view(request, pk):
    tenant = request.tenant
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=tenant, status='draft',
    )
    form = ReeferMaintenanceForm(
        request.POST or None, instance=maintenance, tenant=tenant,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Maintenance {maintenance.maintenance_number} updated successfully.')
        return redirect('cold_chain:reefer_maint_detail', pk=maintenance.pk)

    return render(request, 'cold_chain/reefer_maint_form.html', {
        'form': form,
        'maintenance': maintenance,
        'title': 'Edit Reefer Maintenance',
    })


@login_required
def reefer_maint_delete_view(request, pk):
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        maintenance.delete()
        messages.success(request, 'Reefer Maintenance deleted successfully.')
        return redirect('cold_chain:reefer_maint_list')
    return redirect('cold_chain:reefer_maint_list')


@login_required
def reefer_maint_schedule_view(request, pk):
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        maintenance.status = 'scheduled'
        maintenance.save()
        messages.info(request, f'Maintenance {maintenance.maintenance_number} scheduled.')
    return redirect('cold_chain:reefer_maint_detail', pk=maintenance.pk)


@login_required
def reefer_maint_start_view(request, pk):
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=request.tenant, status='scheduled',
    )
    if request.method == 'POST':
        maintenance.status = 'in_progress'
        maintenance.save()
        messages.info(request, f'Maintenance {maintenance.maintenance_number} started.')
    return redirect('cold_chain:reefer_maint_detail', pk=maintenance.pk)


@login_required
def reefer_maint_complete_view(request, pk):
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=request.tenant, status='in_progress',
    )
    if request.method == 'POST':
        maintenance.status = 'completed'
        maintenance.completed_date = timezone.now().date()
        maintenance.save()
        messages.success(request, f'Maintenance {maintenance.maintenance_number} completed.')
    return redirect('cold_chain:reefer_maint_detail', pk=maintenance.pk)


@login_required
def reefer_maint_cancel_view(request, pk):
    maintenance = get_object_or_404(
        ReeferMaintenance, pk=pk, tenant=request.tenant,
    )
    if maintenance.status not in ('draft', 'scheduled'):
        return redirect('cold_chain:reefer_maint_detail', pk=maintenance.pk)
    if request.method == 'POST':
        maintenance.status = 'cancelled'
        maintenance.save()
        messages.warning(request, f'Maintenance {maintenance.maintenance_number} cancelled.')
    return redirect('cold_chain:reefer_maint_detail', pk=maintenance.pk)
