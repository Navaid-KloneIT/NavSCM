from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AssetDepreciationForm,
    AssetForm,
    AssetSpecificationFormSet,
    BreakdownMaintenanceForm,
    MaintenanceTaskFormSet,
    PreventiveMaintenanceForm,
    SparePartForm,
    SparePartUsageFormSet,
)
from .models import (
    Asset,
    AssetDepreciation,
    BreakdownMaintenance,
    PreventiveMaintenance,
    SparePart,
)


# =============================================================================
# ASSET REGISTRY VIEWS
# =============================================================================

@login_required
def asset_list_view(request):
    tenant = request.tenant
    assets = Asset.objects.filter(tenant=tenant).select_related(
        'assigned_to', 'created_by',
    )
    status_choices = Asset.STATUS_CHOICES
    type_choices = Asset.ASSET_TYPE_CHOICES
    condition_choices = Asset.CONDITION_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        assets = assets.filter(
            Q(asset_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(serial_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        assets = assets.filter(status=status_filter)

    type_filter = request.GET.get('asset_type', '').strip()
    if type_filter:
        assets = assets.filter(asset_type=type_filter)

    condition_filter = request.GET.get('condition', '').strip()
    if condition_filter:
        assets = assets.filter(condition=condition_filter)

    return render(request, 'assets/asset_list.html', {
        'assets': assets,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'condition_choices': condition_choices,
        'search_query': search_query,
    })


@login_required
def asset_create_view(request):
    tenant = request.tenant
    form = AssetForm(request.POST or None, tenant=tenant)
    formset = AssetSpecificationFormSet(request.POST or None, prefix='specs')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        asset = form.save(commit=False)
        asset.tenant = tenant
        asset.created_by = request.user
        asset.save()
        formset.instance = asset
        formset.save()
        messages.success(request, f'Asset {asset.asset_number} created successfully.')
        return redirect('assets:asset_detail', pk=asset.pk)

    return render(request, 'assets/asset_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Asset',
    })


@login_required
def asset_detail_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk, tenant=request.tenant)
    specs = asset.specifications.all()
    depreciations = asset.depreciations.all()

    return render(request, 'assets/asset_detail.html', {
        'asset': asset,
        'specs': specs,
        'depreciations': depreciations,
    })


@login_required
def asset_edit_view(request, pk):
    tenant = request.tenant
    asset = get_object_or_404(Asset, pk=pk, tenant=tenant, status='draft')
    form = AssetForm(request.POST or None, instance=asset, tenant=tenant)
    formset = AssetSpecificationFormSet(
        request.POST or None, instance=asset, prefix='specs',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Asset {asset.asset_number} updated successfully.')
        return redirect('assets:asset_detail', pk=asset.pk)

    return render(request, 'assets/asset_form.html', {
        'form': form,
        'formset': formset,
        'asset': asset,
        'title': 'Edit Asset',
    })


@login_required
def asset_delete_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted successfully.')
        return redirect('assets:asset_list')
    return redirect('assets:asset_list')


@login_required
def asset_activate_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        asset.status = 'active'
        asset.save()
        messages.success(request, f'Asset {asset.asset_number} activated.')
    return redirect('assets:asset_detail', pk=asset.pk)


@login_required
def asset_maintenance_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        asset.status = 'in_maintenance'
        asset.save()
        messages.info(request, f'Asset {asset.asset_number} moved to maintenance.')
    return redirect('assets:asset_detail', pk=asset.pk)


@login_required
def asset_restore_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk, tenant=request.tenant)
    if asset.status not in ('in_maintenance', 'out_of_service'):
        return redirect('assets:asset_detail', pk=asset.pk)
    if request.method == 'POST':
        asset.status = 'active'
        asset.save()
        messages.success(request, f'Asset {asset.asset_number} restored to active.')
    return redirect('assets:asset_detail', pk=asset.pk)


@login_required
def asset_retire_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk, tenant=request.tenant)
    if asset.status in ('draft', 'retired', 'disposed'):
        return redirect('assets:asset_detail', pk=asset.pk)
    if request.method == 'POST':
        asset.status = 'retired'
        asset.save()
        messages.warning(request, f'Asset {asset.asset_number} retired.')
    return redirect('assets:asset_detail', pk=asset.pk)


# =============================================================================
# PREVENTIVE MAINTENANCE VIEWS
# =============================================================================

@login_required
def pm_list_view(request):
    tenant = request.tenant
    schedules = PreventiveMaintenance.objects.filter(tenant=tenant).select_related(
        'asset', 'assigned_to', 'created_by',
    )
    status_choices = PreventiveMaintenance.STATUS_CHOICES
    frequency_choices = PreventiveMaintenance.FREQUENCY_CHOICES
    priority_choices = PreventiveMaintenance.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        schedules = schedules.filter(
            Q(pm_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(asset__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        schedules = schedules.filter(status=status_filter)

    frequency_filter = request.GET.get('frequency', '').strip()
    if frequency_filter:
        schedules = schedules.filter(frequency=frequency_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        schedules = schedules.filter(priority=priority_filter)

    return render(request, 'assets/pm_list.html', {
        'schedules': schedules,
        'status_choices': status_choices,
        'frequency_choices': frequency_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def pm_create_view(request):
    tenant = request.tenant
    form = PreventiveMaintenanceForm(request.POST or None, tenant=tenant)
    formset = MaintenanceTaskFormSet(request.POST or None, prefix='tasks')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        pm = form.save(commit=False)
        pm.tenant = tenant
        pm.created_by = request.user
        pm.save()
        formset.instance = pm
        formset.save()
        messages.success(request, f'PM {pm.pm_number} created successfully.')
        return redirect('assets:pm_detail', pk=pm.pk)

    return render(request, 'assets/pm_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Preventive Maintenance',
    })


@login_required
def pm_detail_view(request, pk):
    pm = get_object_or_404(PreventiveMaintenance, pk=pk, tenant=request.tenant)
    tasks = pm.tasks.all()

    return render(request, 'assets/pm_detail.html', {
        'pm': pm,
        'tasks': tasks,
    })


@login_required
def pm_edit_view(request, pk):
    tenant = request.tenant
    pm = get_object_or_404(PreventiveMaintenance, pk=pk, tenant=tenant, status='draft')
    form = PreventiveMaintenanceForm(request.POST or None, instance=pm, tenant=tenant)
    formset = MaintenanceTaskFormSet(
        request.POST or None, instance=pm, prefix='tasks',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'PM {pm.pm_number} updated successfully.')
        return redirect('assets:pm_detail', pk=pm.pk)

    return render(request, 'assets/pm_form.html', {
        'form': form,
        'formset': formset,
        'pm': pm,
        'title': 'Edit Preventive Maintenance',
    })


@login_required
def pm_delete_view(request, pk):
    pm = get_object_or_404(
        PreventiveMaintenance, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        pm.delete()
        messages.success(request, 'Preventive Maintenance deleted successfully.')
        return redirect('assets:pm_list')
    return redirect('assets:pm_list')


@login_required
def pm_schedule_view(request, pk):
    pm = get_object_or_404(
        PreventiveMaintenance, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        pm.status = 'scheduled'
        pm.save()
        messages.success(request, f'PM {pm.pm_number} scheduled.')
    return redirect('assets:pm_detail', pk=pm.pk)


@login_required
def pm_start_view(request, pk):
    pm = get_object_or_404(
        PreventiveMaintenance, pk=pk, tenant=request.tenant, status='scheduled',
    )
    if request.method == 'POST':
        pm.status = 'in_progress'
        pm.save()
        messages.success(request, f'PM {pm.pm_number} started.')
    return redirect('assets:pm_detail', pk=pm.pk)


@login_required
def pm_complete_view(request, pk):
    pm = get_object_or_404(
        PreventiveMaintenance, pk=pk, tenant=request.tenant, status='in_progress',
    )
    if request.method == 'POST':
        pm.status = 'completed'
        pm.completed_date = timezone.now().date()
        pm.save()
        messages.success(request, f'PM {pm.pm_number} completed.')
    return redirect('assets:pm_detail', pk=pm.pk)


@login_required
def pm_cancel_view(request, pk):
    pm = get_object_or_404(PreventiveMaintenance, pk=pk, tenant=request.tenant)
    if pm.status in ('completed', 'cancelled'):
        return redirect('assets:pm_detail', pk=pm.pk)
    if request.method == 'POST':
        pm.status = 'cancelled'
        pm.save()
        messages.warning(request, f'PM {pm.pm_number} cancelled.')
    return redirect('assets:pm_detail', pk=pm.pk)


# =============================================================================
# BREAKDOWN MAINTENANCE VIEWS
# =============================================================================

@login_required
def bm_list_view(request):
    tenant = request.tenant
    breakdowns = BreakdownMaintenance.objects.filter(tenant=tenant).select_related(
        'asset', 'assigned_to', 'reported_by',
    )
    status_choices = BreakdownMaintenance.STATUS_CHOICES
    severity_choices = BreakdownMaintenance.SEVERITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        breakdowns = breakdowns.filter(
            Q(bm_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(asset__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        breakdowns = breakdowns.filter(status=status_filter)

    severity_filter = request.GET.get('severity', '').strip()
    if severity_filter:
        breakdowns = breakdowns.filter(severity=severity_filter)

    return render(request, 'assets/bm_list.html', {
        'breakdowns': breakdowns,
        'status_choices': status_choices,
        'severity_choices': severity_choices,
        'search_query': search_query,
    })


@login_required
def bm_create_view(request):
    tenant = request.tenant
    form = BreakdownMaintenanceForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        bm = form.save(commit=False)
        bm.tenant = tenant
        bm.reported_by = request.user
        bm.save()
        messages.success(request, f'Breakdown {bm.bm_number} reported successfully.')
        return redirect('assets:bm_detail', pk=bm.pk)

    return render(request, 'assets/bm_form.html', {
        'form': form,
        'title': 'Report Breakdown',
    })


@login_required
def bm_detail_view(request, pk):
    bm = get_object_or_404(BreakdownMaintenance, pk=pk, tenant=request.tenant)
    parts_used = bm.parts_used.select_related('spare_part')

    return render(request, 'assets/bm_detail.html', {
        'bm': bm,
        'parts_used': parts_used,
    })


@login_required
def bm_edit_view(request, pk):
    tenant = request.tenant
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=tenant, status='reported',
    )
    form = BreakdownMaintenanceForm(request.POST or None, instance=bm, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Breakdown {bm.bm_number} updated successfully.')
        return redirect('assets:bm_detail', pk=bm.pk)

    return render(request, 'assets/bm_form.html', {
        'form': form,
        'bm': bm,
        'title': 'Edit Breakdown',
    })


@login_required
def bm_delete_view(request, pk):
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=request.tenant, status='reported',
    )
    if request.method == 'POST':
        bm.delete()
        messages.success(request, 'Breakdown deleted successfully.')
        return redirect('assets:bm_list')
    return redirect('assets:bm_list')


@login_required
def bm_assign_view(request, pk):
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=request.tenant, status='reported',
    )
    if request.method == 'POST':
        bm.status = 'assigned'
        bm.save()
        messages.success(request, f'Breakdown {bm.bm_number} assigned.')
    return redirect('assets:bm_detail', pk=bm.pk)


@login_required
def bm_diagnose_view(request, pk):
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=request.tenant, status='assigned',
    )
    if request.method == 'POST':
        bm.status = 'diagnosing'
        bm.started_date = timezone.now()
        bm.save()
        messages.success(request, f'Breakdown {bm.bm_number} diagnosis started.')
    return redirect('assets:bm_detail', pk=bm.pk)


@login_required
def bm_repair_view(request, pk):
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=request.tenant, status='diagnosing',
    )
    if request.method == 'POST':
        bm.status = 'repairing'
        bm.save()
        messages.success(request, f'Breakdown {bm.bm_number} repair started.')
    return redirect('assets:bm_detail', pk=bm.pk)


@login_required
def bm_complete_view(request, pk):
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=request.tenant, status='repairing',
    )
    if request.method == 'POST':
        bm.status = 'completed'
        bm.completed_date = timezone.now()
        bm.save()
        messages.success(request, f'Breakdown {bm.bm_number} repair completed.')
    return redirect('assets:bm_detail', pk=bm.pk)


@login_required
def bm_close_view(request, pk):
    bm = get_object_or_404(
        BreakdownMaintenance, pk=pk, tenant=request.tenant, status='completed',
    )
    if request.method == 'POST':
        bm.status = 'closed'
        bm.save()
        messages.success(request, f'Breakdown {bm.bm_number} closed.')
    return redirect('assets:bm_detail', pk=bm.pk)


# =============================================================================
# SPARE PARTS INVENTORY VIEWS
# =============================================================================

@login_required
def spare_list_view(request):
    tenant = request.tenant
    parts = SparePart.objects.filter(tenant=tenant).select_related(
        'vendor', 'created_by',
    )
    status_choices = SparePart.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        parts = parts.filter(
            Q(part_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(category__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        parts = parts.filter(status=status_filter)

    return render(request, 'assets/spare_list.html', {
        'parts': parts,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def spare_create_view(request):
    tenant = request.tenant
    form = SparePartForm(request.POST or None, tenant=tenant)
    formset = SparePartUsageFormSet(
        request.POST or None, prefix='usages',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        part = form.save(commit=False)
        part.tenant = tenant
        part.created_by = request.user
        part.save()
        formset.instance = part
        formset.save()
        messages.success(request, f'Spare Part {part.part_number} created successfully.')
        return redirect('assets:spare_detail', pk=part.pk)

    return render(request, 'assets/spare_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Spare Part',
    })


@login_required
def spare_detail_view(request, pk):
    part = get_object_or_404(SparePart, pk=pk, tenant=request.tenant)
    usages = part.usages.select_related('asset', 'breakdown')

    return render(request, 'assets/spare_detail.html', {
        'part': part,
        'usages': usages,
    })


@login_required
def spare_edit_view(request, pk):
    tenant = request.tenant
    part = get_object_or_404(SparePart, pk=pk, tenant=tenant)
    form = SparePartForm(request.POST or None, instance=part, tenant=tenant)
    formset = SparePartUsageFormSet(
        request.POST or None, instance=part, prefix='usages',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Spare Part {part.part_number} updated successfully.')
        return redirect('assets:spare_detail', pk=part.pk)

    return render(request, 'assets/spare_form.html', {
        'form': form,
        'formset': formset,
        'part': part,
        'title': 'Edit Spare Part',
    })


@login_required
def spare_delete_view(request, pk):
    part = get_object_or_404(SparePart, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        part.delete()
        messages.success(request, 'Spare Part deleted successfully.')
        return redirect('assets:spare_list')
    return redirect('assets:spare_list')


# =============================================================================
# ASSET DEPRECIATION VIEWS
# =============================================================================

@login_required
def depreciation_list_view(request):
    tenant = request.tenant
    depreciations = AssetDepreciation.objects.filter(tenant=tenant).select_related(
        'asset', 'created_by',
    )
    status_choices = AssetDepreciation.STATUS_CHOICES
    method_choices = AssetDepreciation.METHOD_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        depreciations = depreciations.filter(
            Q(depreciation_number__icontains=search_query)
            | Q(asset__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        depreciations = depreciations.filter(status=status_filter)

    method_filter = request.GET.get('method', '').strip()
    if method_filter:
        depreciations = depreciations.filter(method=method_filter)

    return render(request, 'assets/depreciation_list.html', {
        'depreciations': depreciations,
        'status_choices': status_choices,
        'method_choices': method_choices,
        'search_query': search_query,
    })


@login_required
def depreciation_create_view(request):
    tenant = request.tenant
    form = AssetDepreciationForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        dep = form.save(commit=False)
        dep.tenant = tenant
        dep.created_by = request.user
        dep.save()
        messages.success(request, f'Depreciation {dep.depreciation_number} created successfully.')
        return redirect('assets:depreciation_detail', pk=dep.pk)

    return render(request, 'assets/depreciation_form.html', {
        'form': form,
        'title': 'New Asset Depreciation',
    })


@login_required
def depreciation_detail_view(request, pk):
    dep = get_object_or_404(AssetDepreciation, pk=pk, tenant=request.tenant)

    return render(request, 'assets/depreciation_detail.html', {
        'dep': dep,
    })


@login_required
def depreciation_edit_view(request, pk):
    tenant = request.tenant
    dep = get_object_or_404(
        AssetDepreciation, pk=pk, tenant=tenant, status='draft',
    )
    form = AssetDepreciationForm(request.POST or None, instance=dep, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Depreciation {dep.depreciation_number} updated successfully.')
        return redirect('assets:depreciation_detail', pk=dep.pk)

    return render(request, 'assets/depreciation_form.html', {
        'form': form,
        'dep': dep,
        'title': 'Edit Asset Depreciation',
    })


@login_required
def depreciation_delete_view(request, pk):
    dep = get_object_or_404(
        AssetDepreciation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        dep.delete()
        messages.success(request, 'Asset Depreciation deleted successfully.')
        return redirect('assets:depreciation_list')
    return redirect('assets:depreciation_list')


@login_required
def depreciation_activate_view(request, pk):
    dep = get_object_or_404(
        AssetDepreciation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        dep.status = 'active'
        dep.save()
        messages.success(request, f'Depreciation {dep.depreciation_number} activated.')
    return redirect('assets:depreciation_detail', pk=dep.pk)


@login_required
def depreciation_fully_depreciated_view(request, pk):
    dep = get_object_or_404(
        AssetDepreciation, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        dep.status = 'fully_depreciated'
        dep.save()
        messages.info(request, f'Depreciation {dep.depreciation_number} marked as fully depreciated.')
    return redirect('assets:depreciation_detail', pk=dep.pk)


@login_required
def depreciation_dispose_view(request, pk):
    dep = get_object_or_404(AssetDepreciation, pk=pk, tenant=request.tenant)
    if dep.status not in ('active', 'fully_depreciated'):
        return redirect('assets:depreciation_detail', pk=dep.pk)
    if request.method == 'POST':
        dep.status = 'disposed'
        dep.save()
        messages.warning(request, f'Depreciation {dep.depreciation_number} marked as disposed.')
    return redirect('assets:depreciation_detail', pk=dep.pk)
