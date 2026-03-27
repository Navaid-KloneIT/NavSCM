from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BillOfMaterialsForm,
    BOMLineItemFormSet,
    MRPRunForm,
    ProductionLogForm,
    ProductionScheduleForm,
    ProductionScheduleItemFormSet,
    WorkCenterForm,
    WorkOrderForm,
    WorkOrderOperationFormSet,
)
from .models import (
    BillOfMaterials,
    MRPRequirement,
    MRPRun,
    ProductionLog,
    ProductionSchedule,
    WorkCenter,
    WorkOrder,
)


# =============================================================================
# WORK CENTER VIEWS
# =============================================================================

@login_required
def workcenter_list_view(request):
    tenant = request.tenant
    work_centers = WorkCenter.objects.filter(tenant=tenant)
    type_choices = WorkCenter.WORK_CENTER_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        work_centers = work_centers.filter(
            Q(name__icontains=search_query)
            | Q(code__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        work_centers = work_centers.filter(work_center_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        work_centers = work_centers.filter(is_active=True)
    elif status_filter == 'inactive':
        work_centers = work_centers.filter(is_active=False)

    return render(request, 'manufacturing/workcenter_list.html', {
        'work_centers': work_centers,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def workcenter_create_view(request):
    tenant = request.tenant
    form = WorkCenterForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        wc = form.save(commit=False)
        wc.tenant = tenant
        wc.save()
        messages.success(request, f'Work Center {wc.code} created successfully.')
        return redirect('manufacturing:workcenter_detail', pk=wc.pk)

    return render(request, 'manufacturing/workcenter_form.html', {
        'form': form,
        'title': 'New Work Center',
    })


@login_required
def workcenter_detail_view(request, pk):
    tenant = request.tenant
    wc = get_object_or_404(WorkCenter, pk=pk, tenant=tenant)
    work_orders = wc.work_orders.select_related('product')[:10]
    logs = wc.production_logs.select_related('work_order', 'operator')[:10]

    return render(request, 'manufacturing/workcenter_detail.html', {
        'wc': wc,
        'work_orders': work_orders,
        'logs': logs,
    })


@login_required
def workcenter_edit_view(request, pk):
    tenant = request.tenant
    wc = get_object_or_404(WorkCenter, pk=pk, tenant=tenant)
    form = WorkCenterForm(request.POST or None, instance=wc, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Work Center {wc.code} updated successfully.')
        return redirect('manufacturing:workcenter_detail', pk=wc.pk)

    return render(request, 'manufacturing/workcenter_form.html', {
        'form': form,
        'wc': wc,
        'title': 'Edit Work Center',
    })


@login_required
def workcenter_delete_view(request, pk):
    wc = get_object_or_404(WorkCenter, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        wc.delete()
        messages.success(request, 'Work Center deleted successfully.')
        return redirect('manufacturing:workcenter_list')
    return redirect('manufacturing:workcenter_list')


# =============================================================================
# BILL OF MATERIALS VIEWS
# =============================================================================

@login_required
def bom_list_view(request):
    tenant = request.tenant
    boms = BillOfMaterials.objects.filter(tenant=tenant).select_related('product', 'created_by')
    status_choices = BillOfMaterials.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        boms = boms.filter(
            Q(bom_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(product__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        boms = boms.filter(status=status_filter)

    return render(request, 'manufacturing/bom_list.html', {
        'boms': boms,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def bom_create_view(request):
    tenant = request.tenant
    form = BillOfMaterialsForm(request.POST or None, tenant=tenant)
    formset = BOMLineItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        bom = form.save(commit=False)
        bom.tenant = tenant
        bom.created_by = request.user
        bom.save()
        formset.instance = bom
        formset.save()
        messages.success(request, f'BOM {bom.bom_number} created successfully.')
        return redirect('manufacturing:bom_detail', pk=bom.pk)

    return render(request, 'manufacturing/bom_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Bill of Materials',
    })


@login_required
def bom_detail_view(request, pk):
    tenant = request.tenant
    bom = get_object_or_404(BillOfMaterials, pk=pk, tenant=tenant)
    line_items = bom.items.select_related('item')

    return render(request, 'manufacturing/bom_detail.html', {
        'bom': bom,
        'line_items': line_items,
    })


@login_required
def bom_edit_view(request, pk):
    tenant = request.tenant
    bom = get_object_or_404(BillOfMaterials, pk=pk, tenant=tenant, status='draft')
    form = BillOfMaterialsForm(request.POST or None, instance=bom, tenant=tenant)
    formset = BOMLineItemFormSet(
        request.POST or None, instance=bom, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'BOM {bom.bom_number} updated successfully.')
        return redirect('manufacturing:bom_detail', pk=bom.pk)

    return render(request, 'manufacturing/bom_form.html', {
        'form': form,
        'formset': formset,
        'bom': bom,
        'title': 'Edit Bill of Materials',
    })


@login_required
def bom_activate_view(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        bom.status = 'active'
        bom.approved_by = request.user
        bom.save()
        messages.success(request, f'BOM {bom.bom_number} activated.')
    return redirect('manufacturing:bom_detail', pk=bom.pk)


@login_required
def bom_obsolete_view(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        bom.status = 'obsolete'
        bom.save()
        messages.success(request, f'BOM {bom.bom_number} marked as obsolete.')
    return redirect('manufacturing:bom_detail', pk=bom.pk)


@login_required
def bom_delete_view(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        bom.delete()
        messages.success(request, 'BOM deleted successfully.')
        return redirect('manufacturing:bom_list')
    return redirect('manufacturing:bom_list')


# =============================================================================
# PRODUCTION SCHEDULE VIEWS
# =============================================================================

@login_required
def schedule_list_view(request):
    tenant = request.tenant
    schedules = ProductionSchedule.objects.filter(tenant=tenant).select_related('created_by')
    status_choices = ProductionSchedule.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        schedules = schedules.filter(
            Q(schedule_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        schedules = schedules.filter(status=status_filter)

    return render(request, 'manufacturing/schedule_list.html', {
        'schedules': schedules,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def schedule_create_view(request):
    tenant = request.tenant
    form = ProductionScheduleForm(request.POST or None, tenant=tenant)
    formset = ProductionScheduleItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        schedule = form.save(commit=False)
        schedule.tenant = tenant
        schedule.created_by = request.user
        schedule.save()
        formset.instance = schedule
        formset.save()
        messages.success(request, f'Schedule {schedule.schedule_number} created successfully.')
        return redirect('manufacturing:schedule_detail', pk=schedule.pk)

    return render(request, 'manufacturing/schedule_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Production Schedule',
    })


@login_required
def schedule_detail_view(request, pk):
    tenant = request.tenant
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=tenant)
    line_items = schedule.items.select_related('product', 'bom', 'work_center')
    work_orders = schedule.work_orders.select_related('product')[:10]

    return render(request, 'manufacturing/schedule_detail.html', {
        'schedule': schedule,
        'line_items': line_items,
        'work_orders': work_orders,
    })


@login_required
def schedule_edit_view(request, pk):
    tenant = request.tenant
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=tenant, status='draft')
    form = ProductionScheduleForm(request.POST or None, instance=schedule, tenant=tenant)
    formset = ProductionScheduleItemFormSet(
        request.POST or None, instance=schedule, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Schedule {schedule.schedule_number} updated successfully.')
        return redirect('manufacturing:schedule_detail', pk=schedule.pk)

    return render(request, 'manufacturing/schedule_form.html', {
        'form': form,
        'formset': formset,
        'schedule': schedule,
        'title': 'Edit Production Schedule',
    })


@login_required
def schedule_plan_view(request, pk):
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        schedule.status = 'planned'
        schedule.save()
        messages.success(request, f'Schedule {schedule.schedule_number} marked as planned.')
    return redirect('manufacturing:schedule_detail', pk=schedule.pk)


@login_required
def schedule_start_view(request, pk):
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=request.tenant, status='planned')
    if request.method == 'POST':
        schedule.status = 'in_progress'
        schedule.save()
        messages.success(request, f'Schedule {schedule.schedule_number} started.')
    return redirect('manufacturing:schedule_detail', pk=schedule.pk)


@login_required
def schedule_complete_view(request, pk):
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=request.tenant, status='in_progress')
    if request.method == 'POST':
        schedule.status = 'completed'
        schedule.save()
        messages.success(request, f'Schedule {schedule.schedule_number} completed.')
    return redirect('manufacturing:schedule_detail', pk=schedule.pk)


@login_required
def schedule_cancel_view(request, pk):
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and schedule.status not in ('completed', 'cancelled'):
        schedule.status = 'cancelled'
        schedule.save()
        messages.success(request, f'Schedule {schedule.schedule_number} cancelled.')
    return redirect('manufacturing:schedule_detail', pk=schedule.pk)


@login_required
def schedule_delete_view(request, pk):
    schedule = get_object_or_404(ProductionSchedule, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted successfully.')
        return redirect('manufacturing:schedule_list')
    return redirect('manufacturing:schedule_list')


# =============================================================================
# WORK ORDER VIEWS
# =============================================================================

@login_required
def workorder_list_view(request):
    tenant = request.tenant
    work_orders = WorkOrder.objects.filter(tenant=tenant).select_related(
        'product', 'work_center', 'created_by',
    )
    status_choices = WorkOrder.STATUS_CHOICES
    priority_choices = WorkOrder.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        work_orders = work_orders.filter(
            Q(work_order_number__icontains=search_query)
            | Q(product__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        work_orders = work_orders.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        work_orders = work_orders.filter(priority=priority_filter)

    return render(request, 'manufacturing/workorder_list.html', {
        'work_orders': work_orders,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def workorder_create_view(request):
    tenant = request.tenant
    form = WorkOrderForm(request.POST or None, tenant=tenant)
    formset = WorkOrderOperationFormSet(
        request.POST or None, prefix='ops',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        wo = form.save(commit=False)
        wo.tenant = tenant
        wo.created_by = request.user
        wo.save()
        formset.instance = wo
        formset.save()
        messages.success(request, f'Work Order {wo.work_order_number} created successfully.')
        return redirect('manufacturing:workorder_detail', pk=wo.pk)

    return render(request, 'manufacturing/workorder_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Work Order',
    })


@login_required
def workorder_detail_view(request, pk):
    tenant = request.tenant
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=tenant)
    operations = wo.operations.select_related('work_center')
    logs = wo.production_logs.select_related('operator', 'work_center')[:10]

    return render(request, 'manufacturing/workorder_detail.html', {
        'wo': wo,
        'operations': operations,
        'logs': logs,
    })


@login_required
def workorder_edit_view(request, pk):
    tenant = request.tenant
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=tenant, status='draft')
    form = WorkOrderForm(request.POST or None, instance=wo, tenant=tenant)
    formset = WorkOrderOperationFormSet(
        request.POST or None, instance=wo, prefix='ops',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Work Order {wo.work_order_number} updated successfully.')
        return redirect('manufacturing:workorder_detail', pk=wo.pk)

    return render(request, 'manufacturing/workorder_form.html', {
        'form': form,
        'formset': formset,
        'wo': wo,
        'title': 'Edit Work Order',
    })


@login_required
def workorder_release_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        wo.status = 'released'
        wo.save()
        messages.success(request, f'Work Order {wo.work_order_number} released.')
    return redirect('manufacturing:workorder_detail', pk=wo.pk)


@login_required
def workorder_start_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant, status='released')
    if request.method == 'POST':
        wo.status = 'in_progress'
        wo.actual_start_date = timezone.now().date()
        wo.save()
        messages.success(request, f'Work Order {wo.work_order_number} started.')
    return redirect('manufacturing:workorder_detail', pk=wo.pk)


@login_required
def workorder_hold_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant, status='in_progress')
    if request.method == 'POST':
        wo.status = 'on_hold'
        wo.save()
        messages.success(request, f'Work Order {wo.work_order_number} put on hold.')
    return redirect('manufacturing:workorder_detail', pk=wo.pk)


@login_required
def workorder_resume_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant, status='on_hold')
    if request.method == 'POST':
        wo.status = 'in_progress'
        wo.save()
        messages.success(request, f'Work Order {wo.work_order_number} resumed.')
    return redirect('manufacturing:workorder_detail', pk=wo.pk)


@login_required
def workorder_complete_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant, status='in_progress')
    if request.method == 'POST':
        wo.status = 'completed'
        wo.actual_end_date = timezone.now().date()
        wo.save()
        messages.success(request, f'Work Order {wo.work_order_number} completed.')
    return redirect('manufacturing:workorder_detail', pk=wo.pk)


@login_required
def workorder_cancel_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and wo.status not in ('completed', 'cancelled'):
        wo.status = 'cancelled'
        wo.save()
        messages.success(request, f'Work Order {wo.work_order_number} cancelled.')
    return redirect('manufacturing:workorder_detail', pk=wo.pk)


@login_required
def workorder_delete_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        wo.delete()
        messages.success(request, 'Work Order deleted successfully.')
        return redirect('manufacturing:workorder_list')
    return redirect('manufacturing:workorder_list')


# =============================================================================
# MRP VIEWS
# =============================================================================

@login_required
def mrp_list_view(request):
    tenant = request.tenant
    mrp_runs = MRPRun.objects.filter(tenant=tenant).select_related('created_by')
    status_choices = MRPRun.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        mrp_runs = mrp_runs.filter(
            Q(mrp_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        mrp_runs = mrp_runs.filter(status=status_filter)

    return render(request, 'manufacturing/mrp_list.html', {
        'mrp_runs': mrp_runs,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def mrp_create_view(request):
    tenant = request.tenant
    form = MRPRunForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        mrp = form.save(commit=False)
        mrp.tenant = tenant
        mrp.created_by = request.user
        mrp.save()
        messages.success(request, f'MRP Run {mrp.mrp_number} created successfully.')
        return redirect('manufacturing:mrp_detail', pk=mrp.pk)

    return render(request, 'manufacturing/mrp_form.html', {
        'form': form,
        'title': 'New MRP Run',
    })


@login_required
def mrp_detail_view(request, pk):
    tenant = request.tenant
    mrp = get_object_or_404(MRPRun, pk=pk, tenant=tenant)
    requirements = mrp.requirements.select_related('item', 'warehouse')

    return render(request, 'manufacturing/mrp_detail.html', {
        'mrp': mrp,
        'requirements': requirements,
    })


@login_required
def mrp_run_view(request, pk):
    """Execute MRP calculation: explode BOMs from active work orders, check inventory."""
    tenant = request.tenant
    mrp = get_object_or_404(MRPRun, pk=pk, tenant=tenant, status='draft')

    if request.method != 'POST':
        return redirect('manufacturing:mrp_detail', pk=mrp.pk)

    try:
        mrp.status = 'running'
        mrp.run_date = timezone.now().date()
        mrp.save()

        # Clear any existing requirements
        mrp.requirements.all().delete()

        # Get active work orders within planning horizon
        horizon_date = timezone.now().date() + timedelta(days=mrp.planning_horizon_days)
        active_orders = WorkOrder.objects.filter(
            tenant=tenant,
            status__in=['released', 'in_progress'],
            planned_start_date__lte=horizon_date,
        ).select_related('bom')

        # Aggregate material requirements from BOMs
        item_requirements = defaultdict(Decimal)
        for wo in active_orders:
            if not wo.bom:
                continue
            remaining = wo.remaining_quantity
            for bom_line in wo.bom.items.select_related('item'):
                if bom_line.item:
                    effective_qty = bom_line.effective_quantity * remaining
                    item_requirements[bom_line.item_id] += effective_qty

        # Calculate net requirements
        from apps.inventory.models import StockItem
        for item_id, required_qty in item_requirements.items():
            on_hand = StockItem.objects.filter(
                tenant=tenant, item_id=item_id,
            ).aggregate(total=Sum('quantity_on_hand'))['total'] or Decimal('0')

            on_order = Decimal('0')
            try:
                from apps.procurement.models import PurchaseOrderItem
                on_order_qs = PurchaseOrderItem.objects.filter(
                    purchase_order__tenant=tenant,
                    purchase_order__status__in=[
                        'approved', 'sent', 'acknowledged', 'partially_received',
                    ],
                    item_id=item_id,
                ).aggregate(
                    total_qty=Sum('quantity'),
                    total_received=Sum('received_quantity'),
                )
                total_qty = on_order_qs['total_qty'] or Decimal('0')
                total_received = on_order_qs['total_received'] or Decimal('0')
                on_order = total_qty - total_received
            except (ImportError, Exception):
                pass

            net = max(Decimal('0'), required_qty - on_hand - on_order)

            MRPRequirement.objects.create(
                mrp_run=mrp,
                item_id=item_id,
                required_quantity=required_qty,
                on_hand_quantity=on_hand,
                on_order_quantity=on_order,
                net_requirement=net,
                planned_order_date=timezone.now().date() + timedelta(days=7),
            )

        mrp.status = 'completed'
        mrp.save()
        messages.success(request, f'MRP Run {mrp.mrp_number} completed. {mrp.total_requirements} requirements generated.')

    except Exception as e:
        mrp.status = 'failed'
        mrp.notes = f"Run failed: {str(e)}"
        mrp.save()
        messages.error(request, f'MRP Run failed: {str(e)}')

    return redirect('manufacturing:mrp_detail', pk=mrp.pk)


@login_required
def mrp_delete_view(request, pk):
    mrp = get_object_or_404(MRPRun, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        mrp.delete()
        messages.success(request, 'MRP Run deleted successfully.')
        return redirect('manufacturing:mrp_list')
    return redirect('manufacturing:mrp_list')


# =============================================================================
# PRODUCTION LOG (SHOP FLOOR) VIEWS
# =============================================================================

@login_required
def log_list_view(request):
    tenant = request.tenant
    logs = ProductionLog.objects.filter(tenant=tenant).select_related(
        'work_order', 'work_center', 'operator',
    )
    type_choices = ProductionLog.LOG_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        logs = logs.filter(
            Q(log_number__icontains=search_query)
            | Q(work_order__work_order_number__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        logs = logs.filter(log_type=type_filter)

    return render(request, 'manufacturing/log_list.html', {
        'logs': logs,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def log_create_view(request):
    tenant = request.tenant
    form = ProductionLogForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.tenant = tenant
        log.save()
        messages.success(request, f'Production Log {log.log_number} created successfully.')
        return redirect('manufacturing:log_detail', pk=log.pk)

    return render(request, 'manufacturing/log_form.html', {
        'form': form,
        'title': 'New Production Log',
    })


@login_required
def log_detail_view(request, pk):
    tenant = request.tenant
    log = get_object_or_404(ProductionLog, pk=pk, tenant=tenant)

    return render(request, 'manufacturing/log_detail.html', {
        'log': log,
    })


@login_required
def log_edit_view(request, pk):
    tenant = request.tenant
    log = get_object_or_404(ProductionLog, pk=pk, tenant=tenant)
    form = ProductionLogForm(request.POST or None, instance=log, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Production Log {log.log_number} updated successfully.')
        return redirect('manufacturing:log_detail', pk=log.pk)

    return render(request, 'manufacturing/log_form.html', {
        'form': form,
        'log': log,
        'title': 'Edit Production Log',
    })


@login_required
def log_delete_view(request, pk):
    log = get_object_or_404(ProductionLog, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        log.delete()
        messages.success(request, 'Production Log deleted successfully.')
        return redirect('manufacturing:log_list')
    return redirect('manufacturing:log_list')
