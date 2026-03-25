from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.inventory.models import Warehouse

from .forms import (
    AllocationItemFormSet,
    CustomerForm,
    OrderAllocationForm,
    OrderForm,
    OrderItemFormSet,
    SalesChannelForm,
)
from .models import (
    Backorder,
    Customer,
    CustomerNotification,
    Order,
    OrderAllocation,
    OrderValidation,
    SalesChannel,
)


# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================

@login_required
def customer_list_view(request):
    tenant = request.tenant
    customers = Customer.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        customers = customers.filter(
            Q(customer_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(company__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        customers = customers.filter(is_active=True)
    elif status_filter == 'inactive':
        customers = customers.filter(is_active=False)

    return render(request, 'oms/customer_list.html', {
        'customers': customers,
        'search_query': search_query,
    })


@login_required
def customer_create_view(request):
    tenant = request.tenant
    form = CustomerForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        customer = form.save(commit=False)
        customer.tenant = tenant
        customer.save()
        messages.success(request, f'Customer {customer.customer_number} created successfully.')
        return redirect('oms:customer_detail', pk=customer.pk)

    return render(request, 'oms/customer_form.html', {
        'form': form,
        'title': 'Add Customer',
    })


@login_required
def customer_detail_view(request, pk):
    tenant = request.tenant
    customer = get_object_or_404(Customer, pk=pk, tenant=tenant)
    orders = customer.orders.all()[:10]

    return render(request, 'oms/customer_detail.html', {
        'customer': customer,
        'orders': orders,
    })


@login_required
def customer_edit_view(request, pk):
    tenant = request.tenant
    customer = get_object_or_404(Customer, pk=pk, tenant=tenant)
    form = CustomerForm(request.POST or None, instance=customer, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Customer {customer.customer_number} updated successfully.')
        return redirect('oms:customer_detail', pk=customer.pk)

    return render(request, 'oms/customer_form.html', {
        'form': form,
        'customer': customer,
        'title': 'Edit Customer',
    })


@login_required
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('oms:customer_list')
    return redirect('oms:customer_list')


# =============================================================================
# SALES CHANNEL MANAGEMENT
# =============================================================================

@login_required
def channel_list_view(request):
    tenant = request.tenant
    channels = SalesChannel.objects.filter(tenant=tenant)
    type_choices = SalesChannel.CHANNEL_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        channels = channels.filter(
            Q(name__icontains=search_query)
        )

    type_filter = request.GET.get('channel_type', '').strip()
    if type_filter:
        channels = channels.filter(channel_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        channels = channels.filter(is_active=True)
    elif status_filter == 'inactive':
        channels = channels.filter(is_active=False)

    return render(request, 'oms/channel_list.html', {
        'channels': channels,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def channel_create_view(request):
    tenant = request.tenant
    form = SalesChannelForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        channel = form.save(commit=False)
        channel.tenant = tenant
        channel.save()
        messages.success(request, f'Sales channel "{channel.name}" created successfully.')
        return redirect('oms:channel_list')

    return render(request, 'oms/channel_form.html', {
        'form': form,
        'title': 'Add Sales Channel',
    })


@login_required
def channel_edit_view(request, pk):
    tenant = request.tenant
    channel = get_object_or_404(SalesChannel, pk=pk, tenant=tenant)
    form = SalesChannelForm(request.POST or None, instance=channel, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Sales channel "{channel.name}" updated successfully.')
        return redirect('oms:channel_list')

    return render(request, 'oms/channel_form.html', {
        'form': form,
        'channel': channel,
        'title': 'Edit Sales Channel',
    })


@login_required
def channel_delete_view(request, pk):
    channel = get_object_or_404(SalesChannel, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        channel.delete()
        messages.success(request, 'Sales channel deleted successfully.')
        return redirect('oms:channel_list')
    return redirect('oms:channel_list')


# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

@login_required
def order_list_view(request):
    tenant = request.tenant
    orders = Order.objects.filter(tenant=tenant).select_related('customer', 'sales_channel')
    status_choices = Order.STATUS_CHOICES
    priority_choices = Order.PRIORITY_CHOICES
    customers = Customer.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query)
            | Q(customer__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders = orders.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        orders = orders.filter(priority=priority_filter)

    customer_filter = request.GET.get('customer', '').strip()
    if customer_filter:
        orders = orders.filter(customer_id=customer_filter)

    return render(request, 'oms/order_list.html', {
        'orders': orders,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'customers': customers,
        'search_query': search_query,
    })


@login_required
def order_create_view(request):
    tenant = request.tenant
    form = OrderForm(request.POST or None, tenant=tenant)
    formset = OrderItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST':
        # Re-init formset with tenant for querysets
        formset = OrderItemFormSet(request.POST, prefix='items')
        for f in formset.forms:
            f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.tenant = tenant
            order.created_by = request.user
            order.save()
            formset.instance = order
            items = formset.save(commit=False)
            for item in items:
                item.total_price = (item.quantity * item.unit_price) + item.tax_amount - item.discount_amount
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            # Recalculate totals
            _recalculate_order_totals(order)
            messages.success(request, f'Order {order.order_number} created successfully.')
            return redirect('oms:order_detail', pk=order.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'oms/order_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Order',
    })


@login_required
def order_detail_view(request, pk):
    tenant = request.tenant
    order = get_object_or_404(Order, pk=pk, tenant=tenant)
    order_items = order.items.select_related('item', 'allocated_warehouse')
    validations = order.validations.all()
    allocations = order.allocations.select_related('warehouse')
    backorders = order.backorders.select_related('item')
    notifications = order.notifications.all()[:5]

    return render(request, 'oms/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'validations': validations,
        'allocations': allocations,
        'backorders': backorders,
        'notifications': notifications,
    })


@login_required
def order_edit_view(request, pk):
    tenant = request.tenant
    order = get_object_or_404(Order, pk=pk, tenant=tenant)

    if order.status not in ('draft', 'on_hold'):
        messages.warning(request, 'Only draft or on-hold orders can be edited.')
        return redirect('oms:order_detail', pk=order.pk)

    form = OrderForm(request.POST or None, instance=order, tenant=tenant)
    formset = OrderItemFormSet(request.POST or None, instance=order, prefix='items')

    if request.method == 'POST':
        for f in formset.forms:
            f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.total_price = (item.quantity * item.unit_price) + item.tax_amount - item.discount_amount
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            _recalculate_order_totals(order)
            messages.success(request, f'Order {order.order_number} updated successfully.')
            return redirect('oms:order_detail', pk=order.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'oms/order_form.html', {
        'form': form,
        'formset': formset,
        'order': order,
        'title': 'Edit Order',
    })


@login_required
def order_delete_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        if order.status != 'draft':
            messages.warning(request, 'Only draft orders can be deleted.')
            return redirect('oms:order_detail', pk=order.pk)
        order.delete()
        messages.success(request, 'Order deleted successfully.')
        return redirect('oms:order_list')
    return redirect('oms:order_list')


def _recalculate_order_totals(order):
    """Recalculate order subtotal, tax, discount, and total from line items."""
    from django.db.models import Sum
    totals = order.items.aggregate(
        subtotal=Sum('total_price'),
        tax=Sum('tax_amount'),
        discount=Sum('discount_amount'),
    )
    order.subtotal = totals['subtotal'] or 0
    order.tax_amount = totals['tax'] or 0
    order.discount_amount = totals['discount'] or 0
    order.total_amount = order.subtotal + order.shipping_amount
    order.save(update_fields=['subtotal', 'tax_amount', 'discount_amount', 'total_amount'])


# =============================================================================
# ORDER WORKFLOW ACTIONS
# =============================================================================

@login_required
def order_submit_validation_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'draft':
        order.status = 'pending_validation'
        order.save()
        messages.success(request, f'Order {order.order_number} submitted for validation.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_validate_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'pending_validation':
        order.status = 'validated'
        order.validated_by = request.user
        order.validated_at = timezone.now()
        order.save()
        messages.success(request, f'Order {order.order_number} validated.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_allocate_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'validated':
        order.status = 'allocated'
        order.save()
        messages.success(request, f'Order {order.order_number} allocated.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_fulfill_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'allocated':
        order.status = 'in_fulfillment'
        order.save()
        messages.success(request, f'Order {order.order_number} moved to fulfillment.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_ship_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status in ('in_fulfillment', 'partially_shipped'):
        order.status = 'shipped'
        order.save()
        messages.success(request, f'Order {order.order_number} marked as shipped.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_deliver_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'shipped':
        order.status = 'delivered'
        order.save()
        messages.success(request, f'Order {order.order_number} marked as delivered.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_cancel_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status not in ('delivered', 'cancelled'):
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order {order.order_number} cancelled.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_hold_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status not in ('delivered', 'cancelled', 'on_hold'):
        order.status = 'on_hold'
        order.save()
        messages.success(request, f'Order {order.order_number} placed on hold.')
    return redirect('oms:order_detail', pk=order.pk)


@login_required
def order_release_view(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and order.status == 'on_hold':
        order.status = 'draft'
        order.save()
        messages.success(request, f'Order {order.order_number} released from hold.')
    return redirect('oms:order_detail', pk=order.pk)


# =============================================================================
# ORDER VALIDATION
# =============================================================================

@login_required
def validation_list_view(request):
    tenant = request.tenant
    validations = OrderValidation.objects.filter(tenant=tenant).select_related('order', 'validated_by')
    status_choices = OrderValidation.STATUS_CHOICES
    type_choices = OrderValidation.VALIDATION_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        validations = validations.filter(
            Q(validation_number__icontains=search_query)
            | Q(order__order_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        validations = validations.filter(status=status_filter)

    type_filter = request.GET.get('validation_type', '').strip()
    if type_filter:
        validations = validations.filter(validation_type=type_filter)

    return render(request, 'oms/validation_list.html', {
        'validations': validations,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def validation_detail_view(request, pk):
    tenant = request.tenant
    validation = get_object_or_404(OrderValidation, pk=pk, tenant=tenant)

    return render(request, 'oms/validation_detail.html', {
        'validation': validation,
    })


@login_required
def validation_pass_view(request, pk):
    validation = get_object_or_404(OrderValidation, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and validation.status == 'pending':
        validation.status = 'passed'
        validation.validated_by = request.user
        validation.validated_at = timezone.now()
        validation.save()
        messages.success(request, f'Validation {validation.validation_number} passed.')
    return redirect('oms:validation_detail', pk=validation.pk)


@login_required
def validation_fail_view(request, pk):
    validation = get_object_or_404(OrderValidation, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and validation.status == 'pending':
        validation.status = 'failed'
        validation.validated_by = request.user
        validation.validated_at = timezone.now()
        validation.save()
        messages.success(request, f'Validation {validation.validation_number} failed.')
    return redirect('oms:validation_detail', pk=validation.pk)


# =============================================================================
# ORDER ALLOCATION
# =============================================================================

@login_required
def allocation_list_view(request):
    tenant = request.tenant
    allocations = OrderAllocation.objects.filter(tenant=tenant).select_related('order', 'warehouse')
    status_choices = OrderAllocation.STATUS_CHOICES
    method_choices = OrderAllocation.ALLOCATION_METHOD_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        allocations = allocations.filter(
            Q(allocation_number__icontains=search_query)
            | Q(order__order_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        allocations = allocations.filter(status=status_filter)

    method_filter = request.GET.get('method', '').strip()
    if method_filter:
        allocations = allocations.filter(allocation_method=method_filter)

    return render(request, 'oms/allocation_list.html', {
        'allocations': allocations,
        'status_choices': status_choices,
        'method_choices': method_choices,
        'search_query': search_query,
    })


@login_required
def allocation_create_view(request):
    tenant = request.tenant
    form = OrderAllocationForm(request.POST or None, tenant=tenant)
    formset = AllocationItemFormSet(request.POST or None, prefix='alloc_items')

    if request.method == 'POST':
        for f in formset.forms:
            f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)
            f.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            allocation = form.save(commit=False)
            allocation.tenant = tenant
            allocation.allocated_by = request.user
            allocation.allocated_at = timezone.now()
            allocation.save()
            formset.instance = allocation
            formset.save()
            messages.success(request, f'Allocation {allocation.allocation_number} created successfully.')
            return redirect('oms:allocation_detail', pk=allocation.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = __import__('apps.procurement.models', fromlist=['Item']).Item.objects.filter(tenant=tenant, is_active=True)
            f.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'oms/allocation_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Allocation',
    })


@login_required
def allocation_detail_view(request, pk):
    tenant = request.tenant
    allocation = get_object_or_404(OrderAllocation, pk=pk, tenant=tenant)
    allocation_items = allocation.items.select_related('item', 'warehouse')

    return render(request, 'oms/allocation_detail.html', {
        'allocation': allocation,
        'allocation_items': allocation_items,
    })


@login_required
def allocation_confirm_view(request, pk):
    allocation = get_object_or_404(OrderAllocation, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and allocation.status == 'pending':
        allocation.status = 'allocated'
        allocation.allocated_by = request.user
        allocation.allocated_at = timezone.now()
        allocation.save()
        messages.success(request, f'Allocation {allocation.allocation_number} confirmed.')
    return redirect('oms:allocation_detail', pk=allocation.pk)


@login_required
def allocation_delete_view(request, pk):
    allocation = get_object_or_404(OrderAllocation, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        if allocation.status != 'pending':
            messages.warning(request, 'Only pending allocations can be deleted.')
            return redirect('oms:allocation_detail', pk=allocation.pk)
        allocation.delete()
        messages.success(request, 'Allocation deleted successfully.')
        return redirect('oms:allocation_list')
    return redirect('oms:allocation_list')


# =============================================================================
# BACKORDER MANAGEMENT
# =============================================================================

@login_required
def backorder_list_view(request):
    tenant = request.tenant
    backorders = Backorder.objects.filter(tenant=tenant).select_related('order', 'item')
    status_choices = Backorder.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        backorders = backorders.filter(
            Q(backorder_number__icontains=search_query)
            | Q(order__order_number__icontains=search_query)
            | Q(item__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        backorders = backorders.filter(status=status_filter)

    return render(request, 'oms/backorder_list.html', {
        'backorders': backorders,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def backorder_detail_view(request, pk):
    tenant = request.tenant
    backorder = get_object_or_404(Backorder, pk=pk, tenant=tenant)

    return render(request, 'oms/backorder_detail.html', {
        'backorder': backorder,
    })


@login_required
def backorder_fulfill_view(request, pk):
    backorder = get_object_or_404(Backorder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and backorder.status in ('pending', 'partially_fulfilled'):
        backorder.status = 'fulfilled'
        backorder.fulfilled_quantity = backorder.quantity
        backorder.save()
        messages.success(request, f'Backorder {backorder.backorder_number} fulfilled.')
    return redirect('oms:backorder_detail', pk=backorder.pk)


@login_required
def backorder_cancel_view(request, pk):
    backorder = get_object_or_404(Backorder, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and backorder.status != 'fulfilled':
        backorder.status = 'cancelled'
        backorder.save()
        messages.success(request, f'Backorder {backorder.backorder_number} cancelled.')
    return redirect('oms:backorder_detail', pk=backorder.pk)


# =============================================================================
# CUSTOMER NOTIFICATIONS
# =============================================================================

@login_required
def notification_list_view(request):
    tenant = request.tenant
    notifications = CustomerNotification.objects.filter(tenant=tenant).select_related('order', 'customer')
    status_choices = CustomerNotification.STATUS_CHOICES
    type_choices = CustomerNotification.NOTIFICATION_TYPE_CHOICES
    channel_choices = CustomerNotification.CHANNEL_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        notifications = notifications.filter(
            Q(notification_number__icontains=search_query)
            | Q(order__order_number__icontains=search_query)
            | Q(customer__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        notifications = notifications.filter(status=status_filter)

    type_filter = request.GET.get('notification_type', '').strip()
    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)

    return render(request, 'oms/notification_list.html', {
        'notifications': notifications,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'channel_choices': channel_choices,
        'search_query': search_query,
    })


@login_required
def notification_detail_view(request, pk):
    tenant = request.tenant
    notification = get_object_or_404(CustomerNotification, pk=pk, tenant=tenant)

    return render(request, 'oms/notification_detail.html', {
        'notification': notification,
    })


@login_required
def notification_send_view(request, pk):
    notification = get_object_or_404(CustomerNotification, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and notification.status == 'pending':
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        messages.success(request, f'Notification {notification.notification_number} sent.')
    return redirect('oms:notification_detail', pk=notification.pk)
