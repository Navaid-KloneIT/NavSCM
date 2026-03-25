from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.procurement.models import Item

from .forms import (
    CarrierForm,
    FreightBillForm,
    FreightBillItemFormSet,
    LoadPlanForm,
    LoadPlanItemFormSet,
    RateCardForm,
    RouteForm,
    ShipmentForm,
    ShipmentItemFormSet,
    ShipmentTrackingForm,
)
from .models import (
    Carrier,
    FreightBill,
    LoadPlan,
    RateCard,
    Route,
    Shipment,
    ShipmentTracking,
    TRANSPORT_MODE_CHOICES,
)


# =============================================================================
# CARRIER MANAGEMENT
# =============================================================================

@login_required
def carrier_list_view(request):
    tenant = request.tenant
    carriers = Carrier.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        carriers = carriers.filter(
            Q(carrier_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(contact_person__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        carriers = carriers.filter(is_active=True)
    elif status_filter == 'inactive':
        carriers = carriers.filter(is_active=False)

    type_filter = request.GET.get('carrier_type', '').strip()
    if type_filter:
        carriers = carriers.filter(carrier_type=type_filter)

    return render(request, 'tms/carrier_list.html', {
        'carriers': carriers,
        'search_query': search_query,
        'carrier_type_choices': Carrier.CARRIER_TYPE_CHOICES,
    })


@login_required
def carrier_create_view(request):
    tenant = request.tenant
    form = CarrierForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        carrier = form.save(commit=False)
        carrier.tenant = tenant
        carrier.save()
        messages.success(request, f'Carrier {carrier.carrier_number} created successfully.')
        return redirect('tms:carrier_detail', pk=carrier.pk)

    return render(request, 'tms/carrier_form.html', {
        'form': form,
        'title': 'Add Carrier',
    })


@login_required
def carrier_detail_view(request, pk):
    tenant = request.tenant
    carrier = get_object_or_404(Carrier, pk=pk, tenant=tenant)
    shipments = carrier.shipments.all()[:10]
    rate_cards = carrier.rate_cards.filter(is_active=True)[:10]

    return render(request, 'tms/carrier_detail.html', {
        'carrier': carrier,
        'shipments': shipments,
        'rate_cards': rate_cards,
    })


@login_required
def carrier_edit_view(request, pk):
    tenant = request.tenant
    carrier = get_object_or_404(Carrier, pk=pk, tenant=tenant)
    form = CarrierForm(request.POST or None, instance=carrier, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Carrier {carrier.carrier_number} updated successfully.')
        return redirect('tms:carrier_detail', pk=carrier.pk)

    return render(request, 'tms/carrier_form.html', {
        'form': form,
        'title': 'Edit Carrier',
        'carrier': carrier,
    })


@login_required
def carrier_delete_view(request, pk):
    tenant = request.tenant
    carrier = get_object_or_404(Carrier, pk=pk, tenant=tenant)
    if request.method == 'POST':
        carrier.delete()
        messages.success(request, 'Carrier deleted successfully.')
        return redirect('tms:carrier_list')
    return redirect('tms:carrier_list')


# =============================================================================
# RATE CARDS
# =============================================================================

@login_required
def rate_list_view(request):
    tenant = request.tenant
    rates = RateCard.objects.filter(tenant=tenant).select_related('carrier')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rates = rates.filter(
            Q(rate_number__icontains=search_query)
            | Q(carrier__name__icontains=search_query)
            | Q(origin__icontains=search_query)
            | Q(destination__icontains=search_query)
        )

    carrier_filter = request.GET.get('carrier', '').strip()
    if carrier_filter:
        rates = rates.filter(carrier_id=carrier_filter)

    mode_filter = request.GET.get('transport_mode', '').strip()
    if mode_filter:
        rates = rates.filter(transport_mode=mode_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        rates = rates.filter(is_active=True)
    elif status_filter == 'inactive':
        rates = rates.filter(is_active=False)

    carriers = Carrier.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/rate_list.html', {
        'rates': rates,
        'search_query': search_query,
        'carriers': carriers,
        'transport_mode_choices': TRANSPORT_MODE_CHOICES,
    })


@login_required
def rate_create_view(request):
    tenant = request.tenant
    form = RateCardForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        rate = form.save(commit=False)
        rate.tenant = tenant
        rate.save()
        messages.success(request, f'Rate Card {rate.rate_number} created successfully.')
        return redirect('tms:rate_detail', pk=rate.pk)

    return render(request, 'tms/rate_form.html', {
        'form': form,
        'title': 'Add Rate Card',
    })


@login_required
def rate_detail_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(RateCard, pk=pk, tenant=tenant)

    return render(request, 'tms/rate_detail.html', {
        'rate': rate,
    })


@login_required
def rate_edit_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(RateCard, pk=pk, tenant=tenant)
    form = RateCardForm(request.POST or None, instance=rate, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Rate Card {rate.rate_number} updated successfully.')
        return redirect('tms:rate_detail', pk=rate.pk)

    return render(request, 'tms/rate_form.html', {
        'form': form,
        'title': 'Edit Rate Card',
        'rate': rate,
    })


@login_required
def rate_delete_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(RateCard, pk=pk, tenant=tenant)
    if request.method == 'POST':
        rate.delete()
        messages.success(request, 'Rate Card deleted successfully.')
        return redirect('tms:rate_list')
    return redirect('tms:rate_list')


# =============================================================================
# ROUTE PLANNING
# =============================================================================

@login_required
def route_list_view(request):
    tenant = request.tenant
    routes = Route.objects.filter(tenant=tenant).select_related('carrier')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        routes = routes.filter(
            Q(route_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(origin__icontains=search_query)
            | Q(destination__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        routes = routes.filter(status=status_filter)

    mode_filter = request.GET.get('transport_mode', '').strip()
    if mode_filter:
        routes = routes.filter(transport_mode=mode_filter)

    return render(request, 'tms/route_list.html', {
        'routes': routes,
        'search_query': search_query,
        'status_choices': Route.STATUS_CHOICES,
        'transport_mode_choices': TRANSPORT_MODE_CHOICES,
    })


@login_required
def route_create_view(request):
    tenant = request.tenant
    form = RouteForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        route = form.save(commit=False)
        route.tenant = tenant
        route.save()
        messages.success(request, f'Route {route.route_number} created successfully.')
        return redirect('tms:route_detail', pk=route.pk)

    return render(request, 'tms/route_form.html', {
        'form': form,
        'title': 'Add Route',
    })


@login_required
def route_detail_view(request, pk):
    tenant = request.tenant
    route = get_object_or_404(Route, pk=pk, tenant=tenant)
    shipments = route.shipments.all()[:10]

    return render(request, 'tms/route_detail.html', {
        'route': route,
        'shipments': shipments,
    })


@login_required
def route_edit_view(request, pk):
    tenant = request.tenant
    route = get_object_or_404(Route, pk=pk, tenant=tenant)
    form = RouteForm(request.POST or None, instance=route, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Route {route.route_number} updated successfully.')
        return redirect('tms:route_detail', pk=route.pk)

    return render(request, 'tms/route_form.html', {
        'form': form,
        'title': 'Edit Route',
        'route': route,
    })


@login_required
def route_delete_view(request, pk):
    tenant = request.tenant
    route = get_object_or_404(Route, pk=pk, tenant=tenant)
    if request.method == 'POST':
        route.delete()
        messages.success(request, 'Route deleted successfully.')
        return redirect('tms:route_list')
    return redirect('tms:route_list')


@login_required
def route_activate_view(request, pk):
    tenant = request.tenant
    route = get_object_or_404(Route, pk=pk, tenant=tenant)
    if request.method == 'POST' and route.status == 'draft':
        route.status = 'active'
        route.save()
        messages.success(request, f'Route {route.route_number} activated.')
    return redirect('tms:route_detail', pk=route.pk)


@login_required
def route_deactivate_view(request, pk):
    tenant = request.tenant
    route = get_object_or_404(Route, pk=pk, tenant=tenant)
    if request.method == 'POST' and route.status == 'active':
        route.status = 'inactive'
        route.save()
        messages.success(request, f'Route {route.route_number} deactivated.')
    return redirect('tms:route_detail', pk=route.pk)


# =============================================================================
# SHIPMENT TRACKING
# =============================================================================

@login_required
def shipment_list_view(request):
    tenant = request.tenant
    shipments = Shipment.objects.filter(tenant=tenant).select_related('carrier', 'route')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        shipments = shipments.filter(
            Q(shipment_number__icontains=search_query)
            | Q(carrier__name__icontains=search_query)
            | Q(current_location__icontains=search_query)
            | Q(origin_address__icontains=search_query)
            | Q(destination_address__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        shipments = shipments.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        shipments = shipments.filter(priority=priority_filter)

    carrier_filter = request.GET.get('carrier', '').strip()
    if carrier_filter:
        shipments = shipments.filter(carrier_id=carrier_filter)

    carriers = Carrier.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/shipment_list.html', {
        'shipments': shipments,
        'search_query': search_query,
        'status_choices': Shipment.STATUS_CHOICES,
        'priority_choices': [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
        'carriers': carriers,
    })


@login_required
def shipment_create_view(request):
    tenant = request.tenant
    form = ShipmentForm(request.POST or None, tenant=tenant)
    formset = ShipmentItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST':
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            shipment = form.save(commit=False)
            shipment.tenant = tenant
            shipment.shipped_by = request.user
            shipment.save()
            formset.instance = shipment
            items = formset.save(commit=False)
            for item in items:
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Shipment {shipment.shipment_number} created successfully.')
            return redirect('tms:shipment_detail', pk=shipment.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/shipment_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Shipment',
    })


@login_required
def shipment_detail_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    items = shipment.items.select_related('item').all()
    tracking_events = shipment.tracking_events.all()[:20]
    freight_bills = shipment.freight_bills.all()[:10]
    load_plans = shipment.load_plans.all()[:10]

    return render(request, 'tms/shipment_detail.html', {
        'shipment': shipment,
        'items': items,
        'tracking_events': tracking_events,
        'freight_bills': freight_bills,
        'load_plans': load_plans,
    })


@login_required
def shipment_edit_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)

    if shipment.status not in ('draft', 'booked'):
        messages.error(request, 'Only draft or booked shipments can be edited.')
        return redirect('tms:shipment_detail', pk=shipment.pk)

    form = ShipmentForm(request.POST or None, instance=shipment, tenant=tenant)
    formset = ShipmentItemFormSet(request.POST or None, instance=shipment, prefix='items')

    if request.method == 'POST':
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Shipment {shipment.shipment_number} updated successfully.')
            return redirect('tms:shipment_detail', pk=shipment.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/shipment_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Shipment',
        'shipment': shipment,
    })


@login_required
def shipment_delete_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    if request.method == 'POST' and shipment.status == 'draft':
        shipment.delete()
        messages.success(request, 'Shipment deleted successfully.')
        return redirect('tms:shipment_list')
    return redirect('tms:shipment_list')


@login_required
def shipment_book_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    if request.method == 'POST' and shipment.status == 'draft':
        shipment.status = 'booked'
        shipment.save()
        messages.success(request, f'Shipment {shipment.shipment_number} booked.')
    return redirect('tms:shipment_detail', pk=shipment.pk)


@login_required
def shipment_pickup_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    if request.method == 'POST' and shipment.status == 'booked':
        shipment.status = 'picked_up'
        shipment.actual_departure = timezone.now()
        shipment.save()
        messages.success(request, f'Shipment {shipment.shipment_number} picked up.')
    return redirect('tms:shipment_detail', pk=shipment.pk)


@login_required
def shipment_transit_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    if request.method == 'POST' and shipment.status == 'picked_up':
        shipment.status = 'in_transit'
        shipment.save()
        messages.success(request, f'Shipment {shipment.shipment_number} is now in transit.')
    return redirect('tms:shipment_detail', pk=shipment.pk)


@login_required
def shipment_deliver_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    if request.method == 'POST' and shipment.status in ('in_transit', 'at_hub', 'out_for_delivery'):
        shipment.status = 'delivered'
        shipment.actual_arrival = timezone.now()
        shipment.save()
        messages.success(request, f'Shipment {shipment.shipment_number} delivered.')
    return redirect('tms:shipment_detail', pk=shipment.pk)


@login_required
def shipment_cancel_view(request, pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=pk, tenant=tenant)
    if request.method == 'POST' and shipment.status not in ('delivered', 'cancelled'):
        shipment.status = 'cancelled'
        shipment.save()
        messages.success(request, f'Shipment {shipment.shipment_number} cancelled.')
    return redirect('tms:shipment_detail', pk=shipment.pk)


# =============================================================================
# SHIPMENT TRACKING EVENTS
# =============================================================================

@login_required
def tracking_list_view(request):
    tenant = request.tenant
    events = ShipmentTracking.objects.filter(
        shipment__tenant=tenant
    ).select_related('shipment', 'recorded_by')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        events = events.filter(
            Q(shipment__shipment_number__icontains=search_query)
            | Q(location__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        events = events.filter(status=status_filter)

    return render(request, 'tms/tracking_list.html', {
        'events': events,
        'search_query': search_query,
        'status_choices': Shipment.STATUS_CHOICES,
    })


@login_required
def tracking_detail_view(request, pk):
    tenant = request.tenant
    event = get_object_or_404(ShipmentTracking, pk=pk, shipment__tenant=tenant)

    return render(request, 'tms/tracking_detail.html', {
        'event': event,
    })


@login_required
def tracking_add_view(request, shipment_pk):
    tenant = request.tenant
    shipment = get_object_or_404(Shipment, pk=shipment_pk, tenant=tenant)
    form = ShipmentTrackingForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.shipment = shipment
        event.recorded_by = request.user
        event.save()
        shipment.current_location = event.location
        shipment.save()
        messages.success(request, 'Tracking event added successfully.')
        return redirect('tms:shipment_detail', pk=shipment.pk)

    return render(request, 'tms/tracking_form.html', {
        'form': form,
        'shipment': shipment,
        'title': 'Add Tracking Event',
    })


# =============================================================================
# FREIGHT AUDIT & PAYMENT
# =============================================================================

@login_required
def freight_list_view(request):
    tenant = request.tenant
    bills = FreightBill.objects.filter(tenant=tenant).select_related('shipment', 'carrier')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        bills = bills.filter(
            Q(bill_number__icontains=search_query)
            | Q(invoice_number__icontains=search_query)
            | Q(carrier__name__icontains=search_query)
            | Q(shipment__shipment_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        bills = bills.filter(status=status_filter)

    carrier_filter = request.GET.get('carrier', '').strip()
    if carrier_filter:
        bills = bills.filter(carrier_id=carrier_filter)

    carriers = Carrier.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/freight_list.html', {
        'bills': bills,
        'search_query': search_query,
        'status_choices': FreightBill.STATUS_CHOICES,
        'carriers': carriers,
    })


@login_required
def freight_create_view(request):
    tenant = request.tenant
    form = FreightBillForm(request.POST or None, tenant=tenant)
    formset = FreightBillItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            bill = form.save(commit=False)
            bill.tenant = tenant
            bill.save()
            formset.instance = bill
            items = formset.save(commit=False)
            for item in items:
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Freight Bill {bill.bill_number} created successfully.')
            return redirect('tms:freight_detail', pk=bill.pk)

    return render(request, 'tms/freight_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Freight Bill',
    })


@login_required
def freight_detail_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    items = bill.items.all()

    return render(request, 'tms/freight_detail.html', {
        'bill': bill,
        'items': items,
    })


@login_required
def freight_edit_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)

    if bill.status not in ('draft', 'pending_review'):
        messages.error(request, 'Only draft or pending review bills can be edited.')
        return redirect('tms:freight_detail', pk=bill.pk)

    form = FreightBillForm(request.POST or None, instance=bill, tenant=tenant)
    formset = FreightBillItemFormSet(request.POST or None, instance=bill, prefix='items')

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Freight Bill {bill.bill_number} updated successfully.')
            return redirect('tms:freight_detail', pk=bill.pk)

    return render(request, 'tms/freight_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Freight Bill',
        'bill': bill,
    })


@login_required
def freight_delete_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    if request.method == 'POST' and bill.status == 'draft':
        bill.delete()
        messages.success(request, 'Freight Bill deleted successfully.')
        return redirect('tms:freight_list')
    return redirect('tms:freight_list')


@login_required
def freight_submit_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    if request.method == 'POST' and bill.status == 'draft':
        bill.status = 'pending_review'
        bill.save()
        messages.success(request, f'Freight Bill {bill.bill_number} submitted for review.')
    return redirect('tms:freight_detail', pk=bill.pk)


@login_required
def freight_approve_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    if request.method == 'POST' and bill.status == 'pending_review':
        bill.status = 'approved'
        bill.audited_by = request.user
        bill.audited_at = timezone.now()
        bill.save()
        messages.success(request, f'Freight Bill {bill.bill_number} approved.')
    return redirect('tms:freight_detail', pk=bill.pk)


@login_required
def freight_dispute_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    if request.method == 'POST' and bill.status == 'pending_review':
        bill.status = 'disputed'
        bill.dispute_reason = request.POST.get('dispute_reason', '')
        bill.audited_by = request.user
        bill.audited_at = timezone.now()
        bill.save()
        messages.success(request, f'Freight Bill {bill.bill_number} disputed.')
    return redirect('tms:freight_detail', pk=bill.pk)


@login_required
def freight_pay_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    if request.method == 'POST' and bill.status == 'approved':
        bill.status = 'paid'
        bill.payment_date = timezone.now().date()
        bill.payment_reference = request.POST.get('payment_reference', '')
        bill.save()
        messages.success(request, f'Freight Bill {bill.bill_number} marked as paid.')
    return redirect('tms:freight_detail', pk=bill.pk)


@login_required
def freight_cancel_view(request, pk):
    tenant = request.tenant
    bill = get_object_or_404(FreightBill, pk=pk, tenant=tenant)
    if request.method == 'POST' and bill.status not in ('paid', 'cancelled'):
        bill.status = 'cancelled'
        bill.save()
        messages.success(request, f'Freight Bill {bill.bill_number} cancelled.')
    return redirect('tms:freight_detail', pk=bill.pk)


# =============================================================================
# LOAD OPTIMIZATION
# =============================================================================

@login_required
def load_list_view(request):
    tenant = request.tenant
    loads = LoadPlan.objects.filter(tenant=tenant).select_related('shipment')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        loads = loads.filter(
            Q(plan_number__icontains=search_query)
            | Q(shipment__shipment_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        loads = loads.filter(status=status_filter)

    vehicle_filter = request.GET.get('vehicle_type', '').strip()
    if vehicle_filter:
        loads = loads.filter(vehicle_type=vehicle_filter)

    return render(request, 'tms/load_list.html', {
        'loads': loads,
        'search_query': search_query,
        'status_choices': LoadPlan.STATUS_CHOICES,
        'vehicle_type_choices': LoadPlan.VEHICLE_TYPE_CHOICES,
    })


@login_required
def load_create_view(request):
    tenant = request.tenant
    form = LoadPlanForm(request.POST or None, tenant=tenant)
    formset = LoadPlanItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST':
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            load = form.save(commit=False)
            load.tenant = tenant
            load.planned_by = request.user
            load.save()
            formset.instance = load
            items = formset.save(commit=False)
            for item in items:
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Load Plan {load.plan_number} created successfully.')
            return redirect('tms:load_detail', pk=load.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/load_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Load Plan',
    })


@login_required
def load_detail_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)
    items = load.items.select_related('item').all()

    return render(request, 'tms/load_detail.html', {
        'load': load,
        'items': items,
    })


@login_required
def load_edit_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)

    if load.status not in ('draft', 'planned'):
        messages.error(request, 'Only draft or planned load plans can be edited.')
        return redirect('tms:load_detail', pk=load.pk)

    form = LoadPlanForm(request.POST or None, instance=load, tenant=tenant)
    formset = LoadPlanItemFormSet(request.POST or None, instance=load, prefix='items')

    if request.method == 'POST':
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Load Plan {load.plan_number} updated successfully.')
            return redirect('tms:load_detail', pk=load.pk)
    else:
        for f in formset.forms:
            f.fields['item'].queryset = Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'tms/load_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Load Plan',
        'load': load,
    })


@login_required
def load_delete_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)
    if request.method == 'POST' and load.status == 'draft':
        load.delete()
        messages.success(request, 'Load Plan deleted successfully.')
        return redirect('tms:load_list')
    return redirect('tms:load_list')


@login_required
def load_plan_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)
    if request.method == 'POST' and load.status == 'draft':
        load.status = 'planned'
        load.save()
        messages.success(request, f'Load Plan {load.plan_number} finalized.')
    return redirect('tms:load_detail', pk=load.pk)


@login_required
def load_start_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)
    if request.method == 'POST' and load.status == 'planned':
        load.status = 'loading'
        load.save()
        messages.success(request, f'Load Plan {load.plan_number} loading started.')
    return redirect('tms:load_detail', pk=load.pk)


@login_required
def load_complete_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)
    if request.method == 'POST' and load.status == 'loading':
        load.status = 'loaded'
        load.save()
        messages.success(request, f'Load Plan {load.plan_number} loading completed.')
    return redirect('tms:load_detail', pk=load.pk)


@login_required
def load_close_view(request, pk):
    tenant = request.tenant
    load = get_object_or_404(LoadPlan, pk=pk, tenant=tenant)
    if request.method == 'POST' and load.status == 'loaded':
        load.status = 'closed'
        load.save()
        messages.success(request, f'Load Plan {load.plan_number} closed.')
    return redirect('tms:load_detail', pk=load.pk)
