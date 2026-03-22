from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.procurement.models import Item

from .forms import (
    InventoryValuationForm,
    ReorderRuleForm,
    StockAdjustmentForm,
    StockAdjustmentItemFormSet,
    WarehouseForm,
    WarehouseLocationForm,
    WarehouseTransferForm,
    WarehouseTransferItemFormSet,
)
from .models import (
    InventoryValuation,
    InventoryValuationItem,
    ReorderRule,
    ReorderSuggestion,
    StockAdjustment,
    StockAdjustmentItem,
    StockItem,
    Warehouse,
    WarehouseLocation,
    WarehouseTransfer,
    WarehouseTransferItem,
)


# =============================================================================
# WAREHOUSE VIEWS
# =============================================================================

@login_required
def warehouse_list_view(request):
    tenant = request.tenant
    warehouses = Warehouse.objects.filter(tenant=tenant)
    type_choices = Warehouse.WAREHOUSE_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        warehouses = warehouses.filter(
            Q(name__icontains=search_query)
            | Q(code__icontains=search_query)
            | Q(city__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        warehouses = warehouses.filter(warehouse_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        warehouses = warehouses.filter(is_active=True)
    elif status_filter == 'inactive':
        warehouses = warehouses.filter(is_active=False)

    return render(request, 'inventory/warehouse_list.html', {
        'warehouses': warehouses,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def warehouse_create_view(request):
    tenant = request.tenant
    form = WarehouseForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        warehouse = form.save(commit=False)
        warehouse.tenant = tenant
        warehouse.save()
        messages.success(request, f'Warehouse {warehouse.code} created successfully.')
        return redirect('inventory:warehouse_detail', pk=warehouse.pk)

    return render(request, 'inventory/warehouse_form.html', {
        'form': form,
        'title': 'Add Warehouse',
    })


@login_required
def warehouse_detail_view(request, pk):
    tenant = request.tenant
    warehouse = get_object_or_404(Warehouse, pk=pk, tenant=tenant)
    locations = warehouse.locations.all()
    stock_items = StockItem.objects.filter(
        tenant=tenant, warehouse=warehouse
    ).select_related('item')

    return render(request, 'inventory/warehouse_detail.html', {
        'warehouse': warehouse,
        'locations': locations,
        'stock_items': stock_items,
    })


@login_required
def warehouse_edit_view(request, pk):
    tenant = request.tenant
    warehouse = get_object_or_404(Warehouse, pk=pk, tenant=tenant)
    form = WarehouseForm(request.POST or None, instance=warehouse, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Warehouse {warehouse.code} updated successfully.')
        return redirect('inventory:warehouse_detail', pk=warehouse.pk)

    return render(request, 'inventory/warehouse_form.html', {
        'form': form,
        'warehouse': warehouse,
        'title': 'Edit Warehouse',
    })


@login_required
def warehouse_delete_view(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        warehouse.delete()
        messages.success(request, 'Warehouse deleted successfully.')
        return redirect('inventory:warehouse_list')
    return redirect('inventory:warehouse_list')


# =============================================================================
# WAREHOUSE LOCATION VIEWS
# =============================================================================

@login_required
def location_create_view(request, warehouse_pk):
    tenant = request.tenant
    warehouse = get_object_or_404(Warehouse, pk=warehouse_pk, tenant=tenant)
    form = WarehouseLocationForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        location = form.save(commit=False)
        location.tenant = tenant
        location.warehouse = warehouse
        location.save()
        messages.success(request, f'Location {location.code} created successfully.')
        return redirect('inventory:warehouse_detail', pk=warehouse.pk)

    return render(request, 'inventory/location_form.html', {
        'form': form,
        'warehouse': warehouse,
        'title': 'Add Location',
    })


@login_required
def location_edit_view(request, pk):
    tenant = request.tenant
    location = get_object_or_404(
        WarehouseLocation.objects.select_related('warehouse'),
        pk=pk, tenant=tenant,
    )
    form = WarehouseLocationForm(request.POST or None, instance=location, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Location {location.code} updated successfully.')
        return redirect('inventory:warehouse_detail', pk=location.warehouse.pk)

    return render(request, 'inventory/location_form.html', {
        'form': form,
        'warehouse': location.warehouse,
        'location': location,
        'title': 'Edit Location',
    })


@login_required
def location_delete_view(request, pk):
    location = get_object_or_404(
        WarehouseLocation.objects.select_related('warehouse'),
        pk=pk, tenant=request.tenant,
    )
    warehouse_pk = location.warehouse.pk
    if request.method == 'POST':
        location.delete()
        messages.success(request, 'Location deleted successfully.')
    return redirect('inventory:warehouse_detail', pk=warehouse_pk)


# =============================================================================
# STOCK ITEM VIEWS
# =============================================================================

@login_required
def stock_list_view(request):
    tenant = request.tenant
    stock_items = StockItem.objects.filter(tenant=tenant).select_related('item', 'warehouse', 'location')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        stock_items = stock_items.filter(
            Q(item__name__icontains=search_query)
            | Q(item__code__icontains=search_query)
            | Q(batch_number__icontains=search_query)
            | Q(serial_number__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        stock_items = stock_items.filter(warehouse_id=warehouse_filter)

    low_stock = request.GET.get('low_stock', '').strip()
    if low_stock == 'yes':
        stock_items = stock_items.filter(
            quantity_on_hand__lte=F('reorder_point'),
            reorder_point__gt=0,
        )

    return render(request, 'inventory/stock_list.html', {
        'stock_items': stock_items,
        'warehouses': warehouses,
        'search_query': search_query,
    })


@login_required
def stock_detail_view(request, pk):
    tenant = request.tenant
    stock_item = get_object_or_404(
        StockItem.objects.select_related('item', 'warehouse', 'location'),
        pk=pk, tenant=tenant,
    )

    return render(request, 'inventory/stock_detail.html', {
        'stock_item': stock_item,
    })


# =============================================================================
# WAREHOUSE TRANSFER VIEWS
# =============================================================================

@login_required
def transfer_list_view(request):
    tenant = request.tenant
    transfers = WarehouseTransfer.objects.filter(tenant=tenant).select_related(
        'source_warehouse', 'destination_warehouse', 'requested_by',
    )
    status_choices = WarehouseTransfer.STATUS_CHOICES
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        transfers = transfers.filter(
            Q(transfer_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        transfers = transfers.filter(status=status_filter)

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        transfers = transfers.filter(
            Q(source_warehouse_id=warehouse_filter)
            | Q(destination_warehouse_id=warehouse_filter)
        )

    return render(request, 'inventory/transfer_list.html', {
        'transfers': transfers,
        'status_choices': status_choices,
        'warehouses': warehouses,
        'search_query': search_query,
    })


@login_required
def transfer_create_view(request):
    tenant = request.tenant
    form = WarehouseTransferForm(request.POST or None, tenant=tenant)
    formset = WarehouseTransferItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        transfer = form.save(commit=False)
        transfer.tenant = tenant
        transfer.requested_by = request.user
        transfer.save()
        formset.instance = transfer
        formset.save()
        messages.success(request, f'Transfer {transfer.transfer_number} created successfully.')
        return redirect('inventory:transfer_detail', pk=transfer.pk)

    return render(request, 'inventory/transfer_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Transfer',
    })


@login_required
def transfer_detail_view(request, pk):
    tenant = request.tenant
    transfer = get_object_or_404(
        WarehouseTransfer.objects.select_related(
            'source_warehouse', 'destination_warehouse', 'requested_by', 'approved_by',
        ),
        pk=pk, tenant=tenant,
    )
    items = transfer.items.select_related('item').all()

    return render(request, 'inventory/transfer_detail.html', {
        'transfer': transfer,
        'items': items,
    })


@login_required
def transfer_edit_view(request, pk):
    tenant = request.tenant
    transfer = get_object_or_404(WarehouseTransfer, pk=pk, tenant=tenant, status='draft')
    form = WarehouseTransferForm(request.POST or None, instance=transfer, tenant=tenant)
    formset = WarehouseTransferItemFormSet(
        request.POST or None, instance=transfer, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Transfer {transfer.transfer_number} updated successfully.')
        return redirect('inventory:transfer_detail', pk=transfer.pk)

    return render(request, 'inventory/transfer_form.html', {
        'form': form,
        'formset': formset,
        'transfer': transfer,
        'title': 'Edit Transfer',
    })


@login_required
def transfer_delete_view(request, pk):
    transfer = get_object_or_404(WarehouseTransfer, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        transfer.delete()
        messages.success(request, 'Transfer deleted successfully.')
        return redirect('inventory:transfer_list')
    return redirect('inventory:transfer_list')


@login_required
def transfer_submit_view(request, pk):
    transfer = get_object_or_404(WarehouseTransfer, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        transfer.status = 'pending'
        transfer.save()
        messages.success(request, f'Transfer {transfer.transfer_number} submitted for approval.')
    return redirect('inventory:transfer_detail', pk=transfer.pk)


@login_required
def transfer_approve_view(request, pk):
    transfer = get_object_or_404(WarehouseTransfer, pk=pk, tenant=request.tenant, status='pending')
    if request.method == 'POST':
        transfer.status = 'in_transit'
        transfer.approved_by = request.user
        transfer.transfer_date = timezone.now().date()
        transfer.save()
        messages.success(request, f'Transfer {transfer.transfer_number} approved and in transit.')
    return redirect('inventory:transfer_detail', pk=transfer.pk)


@login_required
def transfer_receive_view(request, pk):
    transfer = get_object_or_404(WarehouseTransfer, pk=pk, tenant=request.tenant, status='in_transit')
    if request.method == 'POST':
        transfer.status = 'received'
        transfer.received_date = timezone.now().date()
        transfer.save()

        # Update stock levels
        for ti in transfer.items.select_related('item').all():
            qty = ti.quantity_received if ti.quantity_received > 0 else ti.quantity_sent

            # Decrease source
            source_stock, _ = StockItem.objects.get_or_create(
                tenant=request.tenant,
                item=ti.item,
                warehouse=transfer.source_warehouse,
                batch_number='',
                defaults={'quantity_on_hand': 0},
            )
            source_stock.quantity_on_hand -= qty
            source_stock.last_issued_date = timezone.now()
            source_stock.save()

            # Increase destination
            dest_stock, _ = StockItem.objects.get_or_create(
                tenant=request.tenant,
                item=ti.item,
                warehouse=transfer.destination_warehouse,
                batch_number='',
                defaults={'quantity_on_hand': 0},
            )
            dest_stock.quantity_on_hand += qty
            dest_stock.last_received_date = timezone.now()
            dest_stock.save()

        messages.success(request, f'Transfer {transfer.transfer_number} received. Stock updated.')
    return redirect('inventory:transfer_detail', pk=transfer.pk)


@login_required
def transfer_cancel_view(request, pk):
    transfer = get_object_or_404(WarehouseTransfer, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and transfer.status in ('draft', 'pending'):
        transfer.status = 'cancelled'
        transfer.save()
        messages.success(request, f'Transfer {transfer.transfer_number} cancelled.')
    return redirect('inventory:transfer_detail', pk=transfer.pk)


# =============================================================================
# STOCK ADJUSTMENT VIEWS
# =============================================================================

@login_required
def adjustment_list_view(request):
    tenant = request.tenant
    adjustments = StockAdjustment.objects.filter(tenant=tenant).select_related(
        'warehouse', 'adjusted_by',
    )
    status_choices = StockAdjustment.STATUS_CHOICES
    type_choices = StockAdjustment.ADJUSTMENT_TYPE_CHOICES
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        adjustments = adjustments.filter(
            Q(adjustment_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        adjustments = adjustments.filter(status=status_filter)

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        adjustments = adjustments.filter(adjustment_type=type_filter)

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        adjustments = adjustments.filter(warehouse_id=warehouse_filter)

    return render(request, 'inventory/adjustment_list.html', {
        'adjustments': adjustments,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'warehouses': warehouses,
        'search_query': search_query,
    })


@login_required
def adjustment_create_view(request):
    tenant = request.tenant
    form = StockAdjustmentForm(request.POST or None, tenant=tenant)
    formset = StockAdjustmentItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        adjustment = form.save(commit=False)
        adjustment.tenant = tenant
        adjustment.adjusted_by = request.user
        adjustment.save()
        formset.instance = adjustment
        formset.save()
        messages.success(request, f'Adjustment {adjustment.adjustment_number} created successfully.')
        return redirect('inventory:adjustment_detail', pk=adjustment.pk)

    return render(request, 'inventory/adjustment_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Stock Adjustment',
    })


@login_required
def adjustment_detail_view(request, pk):
    tenant = request.tenant
    adjustment = get_object_or_404(
        StockAdjustment.objects.select_related('warehouse', 'adjusted_by', 'approved_by'),
        pk=pk, tenant=tenant,
    )
    items = adjustment.items.select_related('item').all()

    return render(request, 'inventory/adjustment_detail.html', {
        'adjustment': adjustment,
        'items': items,
    })


@login_required
def adjustment_edit_view(request, pk):
    tenant = request.tenant
    adjustment = get_object_or_404(StockAdjustment, pk=pk, tenant=tenant, status='draft')
    form = StockAdjustmentForm(request.POST or None, instance=adjustment, tenant=tenant)
    formset = StockAdjustmentItemFormSet(
        request.POST or None, instance=adjustment, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Adjustment {adjustment.adjustment_number} updated successfully.')
        return redirect('inventory:adjustment_detail', pk=adjustment.pk)

    return render(request, 'inventory/adjustment_form.html', {
        'form': form,
        'formset': formset,
        'adjustment': adjustment,
        'title': 'Edit Stock Adjustment',
    })


@login_required
def adjustment_delete_view(request, pk):
    adjustment = get_object_or_404(StockAdjustment, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        adjustment.delete()
        messages.success(request, 'Adjustment deleted successfully.')
        return redirect('inventory:adjustment_list')
    return redirect('inventory:adjustment_list')


@login_required
def adjustment_submit_view(request, pk):
    adjustment = get_object_or_404(StockAdjustment, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        adjustment.status = 'pending'
        adjustment.save()
        messages.success(request, f'Adjustment {adjustment.adjustment_number} submitted for approval.')
    return redirect('inventory:adjustment_detail', pk=adjustment.pk)


@login_required
def adjustment_approve_view(request, pk):
    adjustment = get_object_or_404(StockAdjustment, pk=pk, tenant=request.tenant, status='pending')
    if request.method == 'POST':
        adjustment.status = 'approved'
        adjustment.approved_by = request.user
        adjustment.save()

        # Apply stock adjustments
        for ai in adjustment.items.select_related('item').all():
            stock, _ = StockItem.objects.get_or_create(
                tenant=request.tenant,
                item=ai.item,
                warehouse=adjustment.warehouse,
                batch_number='',
                defaults={'quantity_on_hand': 0},
            )
            stock.quantity_on_hand = stock.quantity_on_hand + ai.quantity_adjustment
            stock.save()

        messages.success(request, f'Adjustment {adjustment.adjustment_number} approved. Stock updated.')
    return redirect('inventory:adjustment_detail', pk=adjustment.pk)


@login_required
def adjustment_reject_view(request, pk):
    adjustment = get_object_or_404(StockAdjustment, pk=pk, tenant=request.tenant, status='pending')
    if request.method == 'POST':
        adjustment.status = 'rejected'
        adjustment.approved_by = request.user
        adjustment.save()
        messages.success(request, f'Adjustment {adjustment.adjustment_number} rejected.')
    return redirect('inventory:adjustment_detail', pk=adjustment.pk)


# =============================================================================
# REORDER RULE VIEWS
# =============================================================================

@login_required
def reorder_rule_list_view(request):
    tenant = request.tenant
    rules = ReorderRule.objects.filter(tenant=tenant).select_related('item', 'warehouse')
    warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rules = rules.filter(
            Q(item__name__icontains=search_query)
            | Q(item__code__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '').strip()
    if warehouse_filter:
        rules = rules.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        rules = rules.filter(is_active=True)
    elif status_filter == 'inactive':
        rules = rules.filter(is_active=False)

    return render(request, 'inventory/reorder_rule_list.html', {
        'rules': rules,
        'warehouses': warehouses,
        'search_query': search_query,
    })


@login_required
def reorder_rule_create_view(request):
    tenant = request.tenant
    form = ReorderRuleForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        rule = form.save(commit=False)
        rule.tenant = tenant
        rule.save()
        messages.success(request, 'Reorder rule created successfully.')
        return redirect('inventory:reorder_rule_list')

    return render(request, 'inventory/reorder_rule_form.html', {
        'form': form,
        'title': 'Add Reorder Rule',
    })


@login_required
def reorder_rule_edit_view(request, pk):
    tenant = request.tenant
    rule = get_object_or_404(ReorderRule, pk=pk, tenant=tenant)
    form = ReorderRuleForm(request.POST or None, instance=rule, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Reorder rule updated successfully.')
        return redirect('inventory:reorder_rule_list')

    return render(request, 'inventory/reorder_rule_form.html', {
        'form': form,
        'rule': rule,
        'title': 'Edit Reorder Rule',
    })


@login_required
def reorder_rule_delete_view(request, pk):
    rule = get_object_or_404(ReorderRule, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Reorder rule deleted successfully.')
        return redirect('inventory:reorder_rule_list')
    return redirect('inventory:reorder_rule_list')


# =============================================================================
# REORDER SUGGESTION VIEWS
# =============================================================================

@login_required
def reorder_suggestion_list_view(request):
    tenant = request.tenant
    suggestions = ReorderSuggestion.objects.filter(tenant=tenant).select_related(
        'item', 'warehouse', 'rule',
    )
    status_choices = ReorderSuggestion.STATUS_CHOICES

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        suggestions = suggestions.filter(status=status_filter)

    return render(request, 'inventory/reorder_suggestion_list.html', {
        'suggestions': suggestions,
        'status_choices': status_choices,
    })


@login_required
def reorder_suggestion_generate_view(request):
    if request.method == 'POST':
        tenant = request.tenant
        rules = ReorderRule.objects.filter(tenant=tenant, is_active=True).select_related('item', 'warehouse')
        count = 0

        for rule in rules:
            stock = StockItem.objects.filter(
                tenant=tenant,
                item=rule.item,
                warehouse=rule.warehouse,
            ).aggregate(total=Sum('quantity_on_hand'))
            current_qty = stock['total'] or 0

            if current_qty <= rule.reorder_point:
                # Avoid duplicate pending suggestions
                existing = ReorderSuggestion.objects.filter(
                    tenant=tenant,
                    rule=rule,
                    status='pending',
                ).exists()
                if not existing:
                    ReorderSuggestion.objects.create(
                        tenant=tenant,
                        rule=rule,
                        item=rule.item,
                        warehouse=rule.warehouse,
                        suggested_quantity=rule.reorder_quantity,
                        current_stock=current_qty,
                        reorder_point=rule.reorder_point,
                    )
                    rule.last_triggered_at = timezone.now()
                    rule.save()
                    count += 1

        if count:
            messages.success(request, f'{count} reorder suggestion(s) generated.')
        else:
            messages.info(request, 'No items below reorder point. No suggestions generated.')

    return redirect('inventory:reorder_suggestion_list')


@login_required
def reorder_suggestion_approve_view(request, pk):
    suggestion = get_object_or_404(ReorderSuggestion, pk=pk, tenant=request.tenant, status='pending')
    if request.method == 'POST':
        suggestion.status = 'approved'
        suggestion.save()
        messages.success(request, 'Suggestion approved.')
    return redirect('inventory:reorder_suggestion_list')


@login_required
def reorder_suggestion_dismiss_view(request, pk):
    suggestion = get_object_or_404(ReorderSuggestion, pk=pk, tenant=request.tenant, status='pending')
    if request.method == 'POST':
        suggestion.status = 'dismissed'
        suggestion.save()
        messages.success(request, 'Suggestion dismissed.')
    return redirect('inventory:reorder_suggestion_list')


# =============================================================================
# INVENTORY VALUATION VIEWS
# =============================================================================

@login_required
def valuation_list_view(request):
    tenant = request.tenant
    valuations = InventoryValuation.objects.filter(tenant=tenant).select_related(
        'warehouse', 'created_by',
    )
    status_choices = InventoryValuation.STATUS_CHOICES
    method_choices = InventoryValuation.VALUATION_METHOD_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        valuations = valuations.filter(
            Q(valuation_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        valuations = valuations.filter(status=status_filter)

    method_filter = request.GET.get('method', '').strip()
    if method_filter:
        valuations = valuations.filter(valuation_method=method_filter)

    return render(request, 'inventory/valuation_list.html', {
        'valuations': valuations,
        'status_choices': status_choices,
        'method_choices': method_choices,
        'search_query': search_query,
    })


@login_required
def valuation_create_view(request):
    tenant = request.tenant
    form = InventoryValuationForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        valuation = form.save(commit=False)
        valuation.tenant = tenant
        valuation.created_by = request.user
        valuation.save()
        messages.success(request, f'Valuation {valuation.valuation_number} created successfully.')
        return redirect('inventory:valuation_detail', pk=valuation.pk)

    return render(request, 'inventory/valuation_form.html', {
        'form': form,
        'title': 'New Valuation',
    })


@login_required
def valuation_detail_view(request, pk):
    tenant = request.tenant
    valuation = get_object_or_404(
        InventoryValuation.objects.select_related('warehouse', 'created_by'),
        pk=pk, tenant=tenant,
    )
    items = valuation.items.select_related('item', 'warehouse').all()

    return render(request, 'inventory/valuation_detail.html', {
        'valuation': valuation,
        'items': items,
    })


@login_required
def valuation_run_view(request, pk):
    """Run the valuation calculation."""
    valuation = get_object_or_404(
        InventoryValuation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        tenant = request.tenant

        # Clear existing items
        valuation.items.all().delete()

        # Get stock items
        stock_qs = StockItem.objects.filter(tenant=tenant)
        if valuation.warehouse:
            stock_qs = stock_qs.filter(warehouse=valuation.warehouse)

        total_value = 0
        total_items = 0

        for stock in stock_qs.select_related('item', 'warehouse'):
            if stock.quantity_on_hand <= 0:
                continue

            item_value = stock.quantity_on_hand * stock.unit_cost
            InventoryValuationItem.objects.create(
                valuation=valuation,
                item=stock.item,
                warehouse=stock.warehouse,
                quantity_on_hand=stock.quantity_on_hand,
                unit_cost=stock.unit_cost,
                total_value=item_value,
                valuation_method=valuation.valuation_method,
            )
            total_value += item_value
            total_items += 1

        valuation.total_value = total_value
        valuation.total_items = total_items
        valuation.save()

        messages.success(request, f'Valuation calculated: {total_items} items, total value: {total_value:,.2f}')

    return redirect('inventory:valuation_detail', pk=valuation.pk)


@login_required
def valuation_complete_view(request, pk):
    valuation = get_object_or_404(
        InventoryValuation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        valuation.status = 'completed'
        valuation.save()
        messages.success(request, f'Valuation {valuation.valuation_number} completed.')
    return redirect('inventory:valuation_detail', pk=valuation.pk)


@login_required
def valuation_delete_view(request, pk):
    valuation = get_object_or_404(
        InventoryValuation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        valuation.delete()
        messages.success(request, 'Valuation deleted successfully.')
        return redirect('inventory:valuation_list')
    return redirect('inventory:valuation_list')
