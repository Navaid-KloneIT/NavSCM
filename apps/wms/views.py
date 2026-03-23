from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.inventory.models import Warehouse

from .forms import (
    BinForm,
    CycleCountForm,
    CycleCountItemFormSet,
    CycleCountPlanForm,
    DockAppointmentForm,
    PackingOrderForm,
    PickListForm,
    PickListItemFormSet,
    PutAwayTaskForm,
    ReceivingOrderForm,
    ReceivingOrderItemFormSet,
    ShippingLabelForm,
    YardLocationForm,
    YardVisitForm,
)
from .models import (
    Bin,
    CycleCount,
    CycleCountPlan,
    DockAppointment,
    PackingOrder,
    PickList,
    PutAwayTask,
    ReceivingOrder,
    ShippingLabel,
    YardLocation,
    YardVisit,
)


# =============================================================================
# BIN MANAGEMENT
# =============================================================================

@login_required
def bin_list_view(request):
    tenant = request.tenant
    bins = Bin.objects.filter(tenant=tenant).select_related('warehouse')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    type_choices = Bin.BIN_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        bins = bins.filter(
            Q(bin_code__icontains=search_query)
            | Q(zone__icontains=search_query)
            | Q(aisle__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        bins = bins.filter(warehouse_id=warehouse_filter)

    type_filter = request.GET.get('bin_type', '').strip()
    if type_filter:
        bins = bins.filter(bin_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        bins = bins.filter(is_active=True)
    elif status_filter == 'inactive':
        bins = bins.filter(is_active=False)

    return render(request, 'wms/bin_list.html', {
        'bins': bins,
        'warehouses': warehouses,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def bin_create_view(request):
    tenant = request.tenant
    form = BinForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        bin_obj = form.save(commit=False)
        bin_obj.tenant = tenant
        bin_obj.save()
        messages.success(request, f'Bin {bin_obj.bin_code} created successfully.')
        return redirect('wms:bin_detail', pk=bin_obj.pk)

    return render(request, 'wms/bin_form.html', {
        'form': form,
        'title': 'Add Bin',
    })


@login_required
def bin_detail_view(request, pk):
    tenant = request.tenant
    bin_obj = get_object_or_404(Bin, pk=pk, tenant=tenant)

    return render(request, 'wms/bin_detail.html', {
        'bin': bin_obj,
    })


@login_required
def bin_edit_view(request, pk):
    tenant = request.tenant
    bin_obj = get_object_or_404(Bin, pk=pk, tenant=tenant)
    form = BinForm(request.POST or None, instance=bin_obj, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Bin {bin_obj.bin_code} updated successfully.')
        return redirect('wms:bin_detail', pk=bin_obj.pk)

    return render(request, 'wms/bin_form.html', {
        'form': form,
        'bin': bin_obj,
        'title': 'Edit Bin',
    })


@login_required
def bin_delete_view(request, pk):
    bin_obj = get_object_or_404(Bin, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        bin_obj.delete()
        messages.success(request, 'Bin deleted successfully.')
        return redirect('wms:bin_list')
    return redirect('wms:bin_list')


# =============================================================================
# DOCK APPOINTMENT VIEWS
# =============================================================================

@login_required
def dock_list_view(request):
    tenant = request.tenant
    docks = DockAppointment.objects.filter(tenant=tenant).select_related('warehouse')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = DockAppointment.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        docks = docks.filter(
            Q(appointment_number__icontains=search_query)
            | Q(carrier_name__icontains=search_query)
            | Q(trailer_number__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        docks = docks.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        docks = docks.filter(status=status_filter)

    return render(request, 'wms/dock_list.html', {
        'docks': docks,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def dock_create_view(request):
    tenant = request.tenant
    form = DockAppointmentForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        dock = form.save(commit=False)
        dock.tenant = tenant
        dock.save()
        messages.success(request, f'Dock appointment {dock.appointment_number} created.')
        return redirect('wms:dock_detail', pk=dock.pk)

    return render(request, 'wms/dock_form.html', {
        'form': form,
        'title': 'Schedule Dock Appointment',
    })


@login_required
def dock_detail_view(request, pk):
    tenant = request.tenant
    dock = get_object_or_404(DockAppointment, pk=pk, tenant=tenant)
    receiving_orders = dock.receiving_orders.all()

    return render(request, 'wms/dock_detail.html', {
        'dock': dock,
        'receiving_orders': receiving_orders,
    })


@login_required
def dock_edit_view(request, pk):
    tenant = request.tenant
    dock = get_object_or_404(DockAppointment, pk=pk, tenant=tenant)
    form = DockAppointmentForm(request.POST or None, instance=dock, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Dock appointment {dock.appointment_number} updated.')
        return redirect('wms:dock_detail', pk=dock.pk)

    return render(request, 'wms/dock_form.html', {
        'form': form,
        'dock': dock,
        'title': 'Edit Dock Appointment',
    })


@login_required
def dock_delete_view(request, pk):
    dock = get_object_or_404(DockAppointment, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        dock.delete()
        messages.success(request, 'Dock appointment deleted.')
        return redirect('wms:dock_list')
    return redirect('wms:dock_list')


@login_required
def dock_check_in_view(request, pk):
    dock = get_object_or_404(DockAppointment, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and dock.status == 'scheduled':
        dock.status = 'checked_in'
        dock.save()
        messages.success(request, f'{dock.appointment_number} checked in.')
    return redirect('wms:dock_detail', pk=dock.pk)


@login_required
def dock_complete_view(request, pk):
    dock = get_object_or_404(DockAppointment, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and dock.status in ('checked_in', 'receiving'):
        dock.status = 'completed'
        dock.save()
        messages.success(request, f'{dock.appointment_number} completed.')
    return redirect('wms:dock_detail', pk=dock.pk)


@login_required
def dock_cancel_view(request, pk):
    dock = get_object_or_404(DockAppointment, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and dock.status not in ('completed', 'cancelled'):
        dock.status = 'cancelled'
        dock.save()
        messages.success(request, f'{dock.appointment_number} cancelled.')
    return redirect('wms:dock_detail', pk=dock.pk)


# =============================================================================
# RECEIVING ORDER VIEWS
# =============================================================================

@login_required
def receiving_list_view(request):
    tenant = request.tenant
    orders = ReceivingOrder.objects.filter(tenant=tenant).select_related('warehouse', 'dock_appointment')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = ReceivingOrder.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        orders = orders.filter(
            Q(receiving_number__icontains=search_query)
            | Q(supplier_name__icontains=search_query)
            | Q(po_reference__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        orders = orders.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'wms/receiving_list.html', {
        'orders': orders,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def receiving_create_view(request):
    tenant = request.tenant
    form = ReceivingOrderForm(request.POST or None, tenant=tenant)
    formset = ReceivingOrderItemFormSet(request.POST or None, prefix='items')

    # Set tenant on formset forms
    for f in formset.forms:
        f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)
        f.fields['bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        f.fields['bin'].required = False

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        order = form.save(commit=False)
        order.tenant = tenant
        order.save()
        formset.instance = order
        formset.save()
        messages.success(request, f'Receiving order {order.receiving_number} created.')
        return redirect('wms:receiving_detail', pk=order.pk)

    return render(request, 'wms/receiving_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Receiving Order',
    })


@login_required
def receiving_detail_view(request, pk):
    tenant = request.tenant
    order = get_object_or_404(ReceivingOrder, pk=pk, tenant=tenant)
    items = order.items.select_related('item', 'bin')
    putaway_tasks = order.putaway_tasks.select_related('item', 'source_bin', 'destination_bin')

    return render(request, 'wms/receiving_detail.html', {
        'order': order,
        'items': items,
        'putaway_tasks': putaway_tasks,
    })


@login_required
def receiving_edit_view(request, pk):
    tenant = request.tenant
    order = get_object_or_404(ReceivingOrder, pk=pk, tenant=tenant)
    form = ReceivingOrderForm(request.POST or None, instance=order, tenant=tenant)
    formset = ReceivingOrderItemFormSet(request.POST or None, instance=order, prefix='items')

    for f in formset.forms:
        f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)
        f.fields['bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        f.fields['bin'].required = False

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Receiving order {order.receiving_number} updated.')
        return redirect('wms:receiving_detail', pk=order.pk)

    return render(request, 'wms/receiving_form.html', {
        'form': form,
        'formset': formset,
        'order': order,
        'title': 'Edit Receiving Order',
    })


@login_required
def receiving_delete_view(request, pk):
    order = get_object_or_404(ReceivingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Receiving order deleted.')
        return redirect('wms:receiving_list')
    return redirect('wms:receiving_list')


@login_required
def receiving_start_view(request, pk):
    order = get_object_or_404(ReceivingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'pending':
        order.status = 'in_progress'
        order.received_by = request.user
        order.save()
        # Update dock appointment status if linked
        if order.dock_appointment and order.dock_appointment.status == 'checked_in':
            order.dock_appointment.status = 'receiving'
            order.dock_appointment.save()
        messages.success(request, f'{order.receiving_number} started receiving.')
    return redirect('wms:receiving_detail', pk=order.pk)


@login_required
def receiving_complete_view(request, pk):
    order = get_object_or_404(ReceivingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'in_progress':
        order.status = 'completed'
        order.received_at = timezone.now()
        order.save()
        messages.success(request, f'{order.receiving_number} completed.')
    return redirect('wms:receiving_detail', pk=order.pk)


# =============================================================================
# PUT-AWAY TASK VIEWS
# =============================================================================

@login_required
def putaway_list_view(request):
    tenant = request.tenant
    tasks = PutAwayTask.objects.filter(tenant=tenant).select_related(
        'receiving_order', 'item', 'source_bin', 'destination_bin', 'assigned_to'
    )
    status_choices = PutAwayTask.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tasks = tasks.filter(
            Q(task_number__icontains=search_query)
            | Q(item__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    return render(request, 'wms/putaway_list.html', {
        'tasks': tasks,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def putaway_detail_view(request, pk):
    tenant = request.tenant
    task = get_object_or_404(PutAwayTask, pk=pk, tenant=tenant)

    return render(request, 'wms/putaway_detail.html', {
        'task': task,
    })


@login_required
def putaway_start_view(request, pk):
    task = get_object_or_404(PutAwayTask, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and task.status == 'pending':
        task.status = 'in_progress'
        task.assigned_to = request.user
        task.save()
        messages.success(request, f'{task.task_number} started.')
    return redirect('wms:putaway_detail', pk=task.pk)


@login_required
def putaway_complete_view(request, pk):
    task = get_object_or_404(PutAwayTask, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and task.status == 'in_progress':
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        messages.success(request, f'{task.task_number} completed.')
    return redirect('wms:putaway_detail', pk=task.pk)


# =============================================================================
# PICK LIST VIEWS
# =============================================================================

@login_required
def picklist_list_view(request):
    tenant = request.tenant
    pick_lists = PickList.objects.filter(tenant=tenant).select_related('warehouse', 'assigned_to')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = PickList.STATUS_CHOICES
    type_choices = PickList.PICK_TYPE_CHOICES
    priority_choices = PickList.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        pick_lists = pick_lists.filter(
            Q(pick_number__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        pick_lists = pick_lists.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        pick_lists = pick_lists.filter(status=status_filter)

    type_filter = request.GET.get('pick_type', '').strip()
    if type_filter:
        pick_lists = pick_lists.filter(pick_type=type_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        pick_lists = pick_lists.filter(priority=priority_filter)

    return render(request, 'wms/picklist_list.html', {
        'pick_lists': pick_lists,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def picklist_create_view(request):
    tenant = request.tenant
    form = PickListForm(request.POST or None, tenant=tenant)
    formset = PickListItemFormSet(request.POST or None, prefix='items')

    from apps.procurement.models import Item
    for f in formset.forms:
        f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        f.fields['source_bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        f.fields['source_bin'].required = False

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        pick_list = form.save(commit=False)
        pick_list.tenant = tenant
        pick_list.save()
        formset.instance = pick_list
        formset.save()
        messages.success(request, f'Pick list {pick_list.pick_number} created.')
        return redirect('wms:picklist_detail', pk=pick_list.pk)

    return render(request, 'wms/picklist_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Pick List',
    })


@login_required
def picklist_detail_view(request, pk):
    tenant = request.tenant
    pick_list = get_object_or_404(PickList, pk=pk, tenant=tenant)
    items = pick_list.items.select_related('item', 'source_bin')
    packing_orders = pick_list.packing_orders.all()

    return render(request, 'wms/picklist_detail.html', {
        'pick_list': pick_list,
        'items': items,
        'packing_orders': packing_orders,
    })


@login_required
def picklist_edit_view(request, pk):
    tenant = request.tenant
    pick_list = get_object_or_404(PickList, pk=pk, tenant=tenant)
    form = PickListForm(request.POST or None, instance=pick_list, tenant=tenant)
    formset = PickListItemFormSet(request.POST or None, instance=pick_list, prefix='items')

    from apps.procurement.models import Item
    for f in formset.forms:
        f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)
        f.fields['source_bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        f.fields['source_bin'].required = False

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Pick list {pick_list.pick_number} updated.')
        return redirect('wms:picklist_detail', pk=pick_list.pk)

    return render(request, 'wms/picklist_form.html', {
        'form': form,
        'formset': formset,
        'pick_list': pick_list,
        'title': 'Edit Pick List',
    })


@login_required
def picklist_delete_view(request, pk):
    pick_list = get_object_or_404(PickList, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        pick_list.delete()
        messages.success(request, 'Pick list deleted.')
        return redirect('wms:picklist_list')
    return redirect('wms:picklist_list')


@login_required
def picklist_start_view(request, pk):
    pick_list = get_object_or_404(PickList, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and pick_list.status == 'pending':
        pick_list.status = 'in_progress'
        pick_list.started_at = timezone.now()
        pick_list.assigned_to = request.user
        pick_list.save()
        messages.success(request, f'{pick_list.pick_number} started.')
    return redirect('wms:picklist_detail', pk=pick_list.pk)


@login_required
def picklist_complete_view(request, pk):
    pick_list = get_object_or_404(PickList, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and pick_list.status == 'in_progress':
        pick_list.status = 'completed'
        pick_list.completed_at = timezone.now()
        pick_list.save()
        messages.success(request, f'{pick_list.pick_number} completed.')
    return redirect('wms:picklist_detail', pk=pick_list.pk)


# =============================================================================
# PACKING ORDER VIEWS
# =============================================================================

@login_required
def packing_list_view(request):
    tenant = request.tenant
    orders = PackingOrder.objects.filter(tenant=tenant).select_related('warehouse', 'pick_list', 'packer')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = PackingOrder.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        orders = orders.filter(
            Q(packing_number__icontains=search_query)
            | Q(tracking_number__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        orders = orders.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'wms/packing_list.html', {
        'orders': orders,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def packing_create_view(request):
    tenant = request.tenant
    form = PackingOrderForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        order.tenant = tenant
        order.save()
        messages.success(request, f'Packing order {order.packing_number} created.')
        return redirect('wms:packing_detail', pk=order.pk)

    return render(request, 'wms/packing_form.html', {
        'form': form,
        'title': 'New Packing Order',
    })


@login_required
def packing_detail_view(request, pk):
    tenant = request.tenant
    order = get_object_or_404(PackingOrder, pk=pk, tenant=tenant)
    labels = order.shipping_labels.all()

    return render(request, 'wms/packing_detail.html', {
        'order': order,
        'labels': labels,
    })


@login_required
def packing_edit_view(request, pk):
    tenant = request.tenant
    order = get_object_or_404(PackingOrder, pk=pk, tenant=tenant)
    form = PackingOrderForm(request.POST or None, instance=order, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Packing order {order.packing_number} updated.')
        return redirect('wms:packing_detail', pk=order.pk)

    return render(request, 'wms/packing_form.html', {
        'form': form,
        'order': order,
        'title': 'Edit Packing Order',
    })


@login_required
def packing_delete_view(request, pk):
    order = get_object_or_404(PackingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Packing order deleted.')
        return redirect('wms:packing_list')
    return redirect('wms:packing_list')


@login_required
def packing_start_view(request, pk):
    order = get_object_or_404(PackingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'pending':
        order.status = 'packing'
        order.packer = request.user
        order.save()
        messages.success(request, f'{order.packing_number} packing started.')
    return redirect('wms:packing_detail', pk=order.pk)


@login_required
def packing_complete_view(request, pk):
    order = get_object_or_404(PackingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'packing':
        order.status = 'packed'
        order.packed_at = timezone.now()
        order.save()
        messages.success(request, f'{order.packing_number} packing completed.')
    return redirect('wms:packing_detail', pk=order.pk)


@login_required
def packing_ship_view(request, pk):
    order = get_object_or_404(PackingOrder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'packed':
        order.status = 'shipped'
        order.save()
        messages.success(request, f'{order.packing_number} shipped.')
    return redirect('wms:packing_detail', pk=order.pk)


# =============================================================================
# SHIPPING LABEL VIEWS
# =============================================================================

@login_required
def label_list_view(request):
    tenant = request.tenant
    labels = ShippingLabel.objects.filter(tenant=tenant).select_related('packing_order')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        labels = labels.filter(
            Q(label_number__icontains=search_query)
            | Q(carrier__icontains=search_query)
            | Q(tracking_number__icontains=search_query)
        )

    return render(request, 'wms/label_list.html', {
        'labels': labels,
        'search_query': search_query,
    })


@login_required
def label_detail_view(request, pk):
    tenant = request.tenant
    label = get_object_or_404(ShippingLabel, pk=pk, tenant=tenant)

    return render(request, 'wms/label_detail.html', {
        'label': label,
    })


@login_required
def label_generate_view(request, packing_pk):
    tenant = request.tenant
    order = get_object_or_404(PackingOrder, pk=packing_pk, tenant=tenant)
    form = ShippingLabelForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        label = form.save(commit=False)
        label.tenant = tenant
        label.packing_order = order
        label.save()
        messages.success(request, f'Shipping label {label.label_number} generated.')
        return redirect('wms:label_detail', pk=label.pk)

    return render(request, 'wms/label_form.html', {
        'form': form,
        'order': order,
        'title': 'Generate Shipping Label',
    })


# =============================================================================
# CYCLE COUNT PLAN VIEWS
# =============================================================================

@login_required
def plan_list_view(request):
    tenant = request.tenant
    plans = CycleCountPlan.objects.filter(tenant=tenant).select_related('warehouse')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = CycleCountPlan.STATUS_CHOICES
    type_choices = CycleCountPlan.COUNT_TYPE_CHOICES
    frequency_choices = CycleCountPlan.FREQUENCY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        plans = plans.filter(
            Q(plan_number__icontains=search_query)
            | Q(name__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        plans = plans.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        plans = plans.filter(status=status_filter)

    type_filter = request.GET.get('count_type', '').strip()
    if type_filter:
        plans = plans.filter(count_type=type_filter)

    return render(request, 'wms/plan_list.html', {
        'plans': plans,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'frequency_choices': frequency_choices,
        'search_query': search_query,
    })


@login_required
def plan_create_view(request):
    tenant = request.tenant
    form = CycleCountPlanForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        plan = form.save(commit=False)
        plan.tenant = tenant
        plan.save()
        messages.success(request, f'Cycle count plan {plan.plan_number} created.')
        return redirect('wms:plan_detail', pk=plan.pk)

    return render(request, 'wms/plan_form.html', {
        'form': form,
        'title': 'New Cycle Count Plan',
    })


@login_required
def plan_detail_view(request, pk):
    tenant = request.tenant
    plan = get_object_or_404(CycleCountPlan, pk=pk, tenant=tenant)
    cycle_counts = plan.cycle_counts.all()

    return render(request, 'wms/plan_detail.html', {
        'plan': plan,
        'cycle_counts': cycle_counts,
    })


@login_required
def plan_edit_view(request, pk):
    tenant = request.tenant
    plan = get_object_or_404(CycleCountPlan, pk=pk, tenant=tenant)
    form = CycleCountPlanForm(request.POST or None, instance=plan, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Cycle count plan {plan.plan_number} updated.')
        return redirect('wms:plan_detail', pk=plan.pk)

    return render(request, 'wms/plan_form.html', {
        'form': form,
        'plan': plan,
        'title': 'Edit Cycle Count Plan',
    })


@login_required
def plan_delete_view(request, pk):
    plan = get_object_or_404(CycleCountPlan, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Cycle count plan deleted.')
        return redirect('wms:plan_list')
    return redirect('wms:plan_list')


@login_required
def plan_activate_view(request, pk):
    plan = get_object_or_404(CycleCountPlan, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and plan.status in ('draft', 'paused'):
        plan.status = 'active'
        plan.save()
        messages.success(request, f'{plan.plan_number} activated.')
    return redirect('wms:plan_detail', pk=plan.pk)


@login_required
def plan_pause_view(request, pk):
    plan = get_object_or_404(CycleCountPlan, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and plan.status == 'active':
        plan.status = 'paused'
        plan.save()
        messages.success(request, f'{plan.plan_number} paused.')
    return redirect('wms:plan_detail', pk=plan.pk)


# =============================================================================
# CYCLE COUNT VIEWS
# =============================================================================

@login_required
def count_list_view(request):
    tenant = request.tenant
    counts = CycleCount.objects.filter(tenant=tenant).select_related('warehouse', 'plan', 'counter')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = CycleCount.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        counts = counts.filter(
            Q(count_number__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        counts = counts.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        counts = counts.filter(status=status_filter)

    return render(request, 'wms/count_list.html', {
        'counts': counts,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def count_create_view(request):
    tenant = request.tenant
    form = CycleCountForm(request.POST or None, tenant=tenant)
    formset = CycleCountItemFormSet(request.POST or None, prefix='items')

    from apps.procurement.models import Item
    for f in formset.forms:
        f.fields['bin'].queryset = Bin.objects.filter(tenant=tenant, is_active=True)
        f.fields['bin'].required = False
        f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        count = form.save(commit=False)
        count.tenant = tenant
        count.save()
        formset.instance = count
        formset.save()
        messages.success(request, f'Cycle count {count.count_number} created.')
        return redirect('wms:count_detail', pk=count.pk)

    return render(request, 'wms/count_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Cycle Count',
    })


@login_required
def count_detail_view(request, pk):
    tenant = request.tenant
    count = get_object_or_404(CycleCount, pk=pk, tenant=tenant)
    items = count.items.select_related('bin', 'item', 'counted_by')

    return render(request, 'wms/count_detail.html', {
        'count': count,
        'items': items,
    })


@login_required
def count_start_view(request, pk):
    count = get_object_or_404(CycleCount, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and count.status == 'pending':
        count.status = 'in_progress'
        count.started_at = timezone.now()
        count.counter = request.user
        count.save()
        messages.success(request, f'{count.count_number} started.')
    return redirect('wms:count_detail', pk=count.pk)


@login_required
def count_complete_view(request, pk):
    count = get_object_or_404(CycleCount, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and count.status == 'in_progress':
        count.status = 'completed'
        count.completed_at = timezone.now()
        # Calculate summary
        items = count.items.all()
        count.total_items = items.count()
        count.items_counted = items.exclude(counted_quantity=0).count()
        count.variance_count = items.exclude(variance=0).count()
        count.save()
        messages.success(request, f'{count.count_number} completed.')
    return redirect('wms:count_detail', pk=count.pk)


# =============================================================================
# YARD LOCATION VIEWS
# =============================================================================

@login_required
def yard_location_list_view(request):
    tenant = request.tenant
    locations = YardLocation.objects.filter(tenant=tenant).select_related('warehouse')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    type_choices = YardLocation.LOCATION_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        locations = locations.filter(
            Q(location_code__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        locations = locations.filter(warehouse_id=warehouse_filter)

    type_filter = request.GET.get('location_type', '').strip()
    if type_filter:
        locations = locations.filter(location_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        locations = locations.filter(is_active=True)
    elif status_filter == 'inactive':
        locations = locations.filter(is_active=False)

    return render(request, 'wms/yard_location_list.html', {
        'locations': locations,
        'warehouses': warehouses,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def yard_location_create_view(request):
    tenant = request.tenant
    form = YardLocationForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        location = form.save(commit=False)
        location.tenant = tenant
        location.save()
        messages.success(request, f'Yard location {location.location_code} created.')
        return redirect('wms:yard_location_detail', pk=location.pk)

    return render(request, 'wms/yard_location_form.html', {
        'form': form,
        'title': 'Add Yard Location',
    })


@login_required
def yard_location_detail_view(request, pk):
    tenant = request.tenant
    location = get_object_or_404(YardLocation, pk=pk, tenant=tenant)
    visits = location.visits.select_related('warehouse').order_by('-created_at')[:10]

    return render(request, 'wms/yard_location_detail.html', {
        'location': location,
        'visits': visits,
    })


@login_required
def yard_location_edit_view(request, pk):
    tenant = request.tenant
    location = get_object_or_404(YardLocation, pk=pk, tenant=tenant)
    form = YardLocationForm(request.POST or None, instance=location, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Yard location {location.location_code} updated.')
        return redirect('wms:yard_location_detail', pk=location.pk)

    return render(request, 'wms/yard_location_form.html', {
        'form': form,
        'location': location,
        'title': 'Edit Yard Location',
    })


@login_required
def yard_location_delete_view(request, pk):
    location = get_object_or_404(YardLocation, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        location.delete()
        messages.success(request, 'Yard location deleted.')
        return redirect('wms:yard_location_list')
    return redirect('wms:yard_location_list')


# =============================================================================
# YARD VISIT VIEWS
# =============================================================================

@login_required
def yard_visit_list_view(request):
    tenant = request.tenant
    visits = YardVisit.objects.filter(tenant=tenant).select_related('warehouse', 'yard_location', 'appointment')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)
    status_choices = YardVisit.STATUS_CHOICES
    type_choices = YardVisit.VISIT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        visits = visits.filter(
            Q(visit_number__icontains=search_query)
            | Q(carrier_name__icontains=search_query)
            | Q(driver_name__icontains=search_query)
            | Q(trailer_number__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        visits = visits.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        visits = visits.filter(status=status_filter)

    type_filter = request.GET.get('visit_type', '').strip()
    if type_filter:
        visits = visits.filter(visit_type=type_filter)

    return render(request, 'wms/yard_visit_list.html', {
        'visits': visits,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def yard_visit_create_view(request):
    tenant = request.tenant
    form = YardVisitForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        visit = form.save(commit=False)
        visit.tenant = tenant
        visit.save()
        messages.success(request, f'Yard visit {visit.visit_number} created.')
        return redirect('wms:yard_visit_detail', pk=visit.pk)

    return render(request, 'wms/yard_visit_form.html', {
        'form': form,
        'title': 'New Yard Visit',
    })


@login_required
def yard_visit_detail_view(request, pk):
    tenant = request.tenant
    visit = get_object_or_404(YardVisit, pk=pk, tenant=tenant)

    return render(request, 'wms/yard_visit_detail.html', {
        'visit': visit,
    })


@login_required
def yard_visit_check_in_view(request, pk):
    visit = get_object_or_404(YardVisit, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and visit.status == 'expected':
        visit.status = 'checked_in'
        visit.check_in_time = timezone.now()
        visit.save()
        # Mark yard location as occupied
        if visit.yard_location:
            visit.yard_location.is_occupied = True
            visit.yard_location.save()
        messages.success(request, f'{visit.visit_number} checked in.')
    return redirect('wms:yard_visit_detail', pk=visit.pk)


@login_required
def yard_visit_dock_view(request, pk):
    visit = get_object_or_404(YardVisit, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and visit.status == 'checked_in':
        visit.status = 'at_dock'
        visit.save()
        messages.success(request, f'{visit.visit_number} moved to dock.')
    return redirect('wms:yard_visit_detail', pk=visit.pk)


@login_required
def yard_visit_complete_view(request, pk):
    visit = get_object_or_404(YardVisit, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and visit.status in ('at_dock', 'loading', 'unloading'):
        visit.status = 'completed'
        visit.save()
        messages.success(request, f'{visit.visit_number} completed.')
    return redirect('wms:yard_visit_detail', pk=visit.pk)


@login_required
def yard_visit_depart_view(request, pk):
    visit = get_object_or_404(YardVisit, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and visit.status == 'completed':
        visit.status = 'departed'
        visit.check_out_time = timezone.now()
        visit.save()
        # Free yard location
        if visit.yard_location:
            visit.yard_location.is_occupied = False
            visit.yard_location.save()
        messages.success(request, f'{visit.visit_number} departed.')
    return redirect('wms:yard_visit_detail', pk=visit.pk)
