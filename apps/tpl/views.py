from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    BillingInvoiceForm,
    BillingInvoiceItemFormSet,
    BillingRateForm,
    ClientForm,
    ClientInventoryItemForm,
    ClientStorageZoneForm,
    IntegrationConfigForm,
    RentalAgreementForm,
    SLAForm,
    SLAMetricFormSet,
    SpaceUsageRecordFormSet,
)
from .models import (
    BillingInvoice,
    BillingRate,
    Client,
    ClientInventoryItem,
    ClientStorageZone,
    IntegrationConfig,
    RentalAgreement,
    SLA,
)


# =============================================================================
# Client Views
# =============================================================================

@login_required
def client_list_view(request):
    tenant = request.tenant
    clients = Client.objects.filter(tenant=tenant).select_related('created_by')
    status_choices = Client.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        clients = clients.filter(
            Q(client_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(contact_person__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        clients = clients.filter(status=status_filter)

    return render(request, 'tpl/client_list.html', {
        'clients': clients,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def client_create_view(request):
    tenant = request.tenant
    form = ClientForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)
        client.tenant = tenant
        client.created_by = request.user
        client.save()
        messages.success(request, f'Client {client.client_number} created successfully.')
        return redirect('tpl:client_detail', pk=client.pk)

    return render(request, 'tpl/client_form.html', {
        'form': form,
        'title': 'New Client',
    })


@login_required
def client_detail_view(request, pk):
    client = get_object_or_404(Client, pk=pk, tenant=request.tenant)
    return render(request, 'tpl/client_detail.html', {
        'client': client,
        'billing_rates': client.billing_rates.all()[:5],
        'invoices': client.billing_invoices.all()[:5],
        'storage_zones': client.storage_zones.all()[:5],
        'slas': client.slas.all()[:5],
        'integrations': client.integrations.all()[:5],
        'rental_agreements': client.rental_agreements.all()[:5],
    })


@login_required
def client_edit_view(request, pk):
    tenant = request.tenant
    client = get_object_or_404(Client, pk=pk, tenant=tenant, status='draft')
    form = ClientForm(request.POST or None, instance=client)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Client {client.client_number} updated successfully.')
        return redirect('tpl:client_detail', pk=client.pk)

    return render(request, 'tpl/client_form.html', {
        'form': form,
        'client': client,
        'title': 'Edit Client',
    })


@login_required
def client_delete_view(request, pk):
    client = get_object_or_404(Client, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client deleted successfully.')
        return redirect('tpl:client_list')
    return redirect('tpl:client_list')


@login_required
def client_activate_view(request, pk):
    client = get_object_or_404(Client, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        client.status = 'active'
        client.save()
        messages.success(request, f'Client {client.client_number} activated.')
    return redirect('tpl:client_detail', pk=client.pk)


@login_required
def client_suspend_view(request, pk):
    client = get_object_or_404(Client, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        client.status = 'suspended'
        client.save()
        messages.success(request, f'Client {client.client_number} suspended.')
    return redirect('tpl:client_detail', pk=client.pk)


@login_required
def client_terminate_view(request, pk):
    client = get_object_or_404(Client, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and client.status in ('active', 'suspended'):
        client.status = 'terminated'
        client.save()
        messages.success(request, f'Client {client.client_number} terminated.')
    return redirect('tpl:client_detail', pk=client.pk)


# =============================================================================
# Billing Rate Views
# =============================================================================

@login_required
def billing_rate_list_view(request):
    tenant = request.tenant
    rates = BillingRate.objects.filter(tenant=tenant).select_related('client', 'created_by')
    rate_type_choices = BillingRate.RATE_TYPE_CHOICES
    clients = Client.objects.filter(tenant=tenant, status='active')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rates = rates.filter(
            Q(rate_number__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        rates = rates.filter(rate_type=type_filter)

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        rates = rates.filter(client_id=client_filter)

    active_filter = request.GET.get('active', '').strip()
    if active_filter == 'yes':
        rates = rates.filter(is_active=True)
    elif active_filter == 'no':
        rates = rates.filter(is_active=False)

    return render(request, 'tpl/billing_rate_list.html', {
        'rates': rates,
        'rate_type_choices': rate_type_choices,
        'clients': clients,
        'search_query': search_query,
    })


@login_required
def billing_rate_create_view(request):
    tenant = request.tenant
    form = BillingRateForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        rate = form.save(commit=False)
        rate.tenant = tenant
        rate.created_by = request.user
        rate.save()
        messages.success(request, f'Billing rate {rate.rate_number} created successfully.')
        return redirect('tpl:billing_rate_detail', pk=rate.pk)

    return render(request, 'tpl/billing_rate_form.html', {
        'form': form,
        'title': 'New Billing Rate',
    })


@login_required
def billing_rate_detail_view(request, pk):
    rate = get_object_or_404(BillingRate, pk=pk, tenant=request.tenant)
    return render(request, 'tpl/billing_rate_detail.html', {'rate': rate})


@login_required
def billing_rate_edit_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(BillingRate, pk=pk, tenant=tenant)
    form = BillingRateForm(request.POST or None, instance=rate, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Billing rate {rate.rate_number} updated successfully.')
        return redirect('tpl:billing_rate_detail', pk=rate.pk)

    return render(request, 'tpl/billing_rate_form.html', {
        'form': form,
        'rate': rate,
        'title': 'Edit Billing Rate',
    })


@login_required
def billing_rate_delete_view(request, pk):
    rate = get_object_or_404(BillingRate, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        rate.delete()
        messages.success(request, 'Billing rate deleted successfully.')
        return redirect('tpl:billing_rate_list')
    return redirect('tpl:billing_rate_list')


# =============================================================================
# Billing Invoice Views
# =============================================================================

@login_required
def billing_invoice_list_view(request):
    tenant = request.tenant
    invoices = BillingInvoice.objects.filter(tenant=tenant).select_related('client', 'created_by')
    status_choices = BillingInvoice.STATUS_CHOICES
    clients = Client.objects.filter(tenant=tenant, status='active')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        invoices = invoices.filter(client_id=client_filter)

    return render(request, 'tpl/billing_invoice_list.html', {
        'invoices': invoices,
        'status_choices': status_choices,
        'clients': clients,
        'search_query': search_query,
    })


@login_required
def billing_invoice_create_view(request):
    tenant = request.tenant
    form = BillingInvoiceForm(request.POST or None, tenant=tenant)
    formset = BillingInvoiceItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        invoice = form.save(commit=False)
        invoice.tenant = tenant
        invoice.created_by = request.user
        invoice.save()
        formset.instance = invoice
        formset.save()
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
        return redirect('tpl:billing_invoice_detail', pk=invoice.pk)

    return render(request, 'tpl/billing_invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Invoice',
    })


@login_required
def billing_invoice_detail_view(request, pk):
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=request.tenant)
    line_items = invoice.line_items.select_related('rate')
    return render(request, 'tpl/billing_invoice_detail.html', {
        'invoice': invoice,
        'line_items': line_items,
    })


@login_required
def billing_invoice_edit_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=tenant, status='draft')
    form = BillingInvoiceForm(request.POST or None, instance=invoice, tenant=tenant)
    formset = BillingInvoiceItemFormSet(request.POST or None, instance=invoice, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Invoice {invoice.invoice_number} updated successfully.')
        return redirect('tpl:billing_invoice_detail', pk=invoice.pk)

    return render(request, 'tpl/billing_invoice_form.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice,
        'title': 'Edit Invoice',
    })


@login_required
def billing_invoice_delete_view(request, pk):
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully.')
        return redirect('tpl:billing_invoice_list')
    return redirect('tpl:billing_invoice_list')


@login_required
def billing_invoice_send_view(request, pk):
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        invoice.status = 'sent'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} marked as sent.')
    return redirect('tpl:billing_invoice_detail', pk=invoice.pk)


@login_required
def billing_invoice_paid_view(request, pk):
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and invoice.status in ('sent', 'overdue'):
        invoice.status = 'paid'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} marked as paid.')
    return redirect('tpl:billing_invoice_detail', pk=invoice.pk)


@login_required
def billing_invoice_overdue_view(request, pk):
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=request.tenant, status='sent')
    if request.method == 'POST':
        invoice.status = 'overdue'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} marked as overdue.')
    return redirect('tpl:billing_invoice_detail', pk=invoice.pk)


@login_required
def billing_invoice_cancel_view(request, pk):
    invoice = get_object_or_404(BillingInvoice, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and invoice.status in ('draft', 'sent', 'overdue'):
        invoice.status = 'cancelled'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} cancelled.')
    return redirect('tpl:billing_invoice_detail', pk=invoice.pk)


# =============================================================================
# Client Storage Zone Views
# =============================================================================

@login_required
def storage_zone_list_view(request):
    tenant = request.tenant
    zones = ClientStorageZone.objects.filter(tenant=tenant).select_related('client', 'warehouse', 'created_by')
    zone_type_choices = ClientStorageZone.ZONE_TYPE_CHOICES
    clients = Client.objects.filter(tenant=tenant, status='active')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        zones = zones.filter(
            Q(zone_number__icontains=search_query)
            | Q(zone_name__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        zones = zones.filter(zone_type=type_filter)

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        zones = zones.filter(client_id=client_filter)

    active_filter = request.GET.get('active', '').strip()
    if active_filter == 'yes':
        zones = zones.filter(is_active=True)
    elif active_filter == 'no':
        zones = zones.filter(is_active=False)

    return render(request, 'tpl/storage_zone_list.html', {
        'zones': zones,
        'zone_type_choices': zone_type_choices,
        'clients': clients,
        'search_query': search_query,
    })


@login_required
def storage_zone_create_view(request):
    tenant = request.tenant
    form = ClientStorageZoneForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        zone = form.save(commit=False)
        zone.tenant = tenant
        zone.created_by = request.user
        zone.save()
        messages.success(request, f'Storage zone {zone.zone_number} created successfully.')
        return redirect('tpl:storage_zone_detail', pk=zone.pk)

    return render(request, 'tpl/storage_zone_form.html', {
        'form': form,
        'title': 'New Storage Zone',
    })


@login_required
def storage_zone_detail_view(request, pk):
    zone = get_object_or_404(ClientStorageZone, pk=pk, tenant=request.tenant)
    inventory_items = zone.inventory_items.all()
    return render(request, 'tpl/storage_zone_detail.html', {
        'zone': zone,
        'inventory_items': inventory_items,
    })


@login_required
def storage_zone_edit_view(request, pk):
    tenant = request.tenant
    zone = get_object_or_404(ClientStorageZone, pk=pk, tenant=tenant)
    form = ClientStorageZoneForm(request.POST or None, instance=zone, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Storage zone {zone.zone_number} updated successfully.')
        return redirect('tpl:storage_zone_detail', pk=zone.pk)

    return render(request, 'tpl/storage_zone_form.html', {
        'form': form,
        'zone': zone,
        'title': 'Edit Storage Zone',
    })


@login_required
def storage_zone_delete_view(request, pk):
    zone = get_object_or_404(ClientStorageZone, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        zone.delete()
        messages.success(request, 'Storage zone deleted successfully.')
        return redirect('tpl:storage_zone_list')
    return redirect('tpl:storage_zone_list')


# =============================================================================
# Client Inventory Item Views
# =============================================================================

@login_required
def client_inventory_list_view(request):
    tenant = request.tenant
    items = ClientInventoryItem.objects.filter(tenant=tenant).select_related('client', 'storage_zone', 'created_by')
    clients = Client.objects.filter(tenant=tenant, status='active')
    zones = ClientStorageZone.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        items = items.filter(
            Q(tracking_number__icontains=search_query)
            | Q(item_name__icontains=search_query)
            | Q(sku__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        items = items.filter(client_id=client_filter)

    zone_filter = request.GET.get('zone', '').strip()
    if zone_filter:
        items = items.filter(storage_zone_id=zone_filter)

    return render(request, 'tpl/client_inventory_list.html', {
        'items': items,
        'clients': clients,
        'zones': zones,
        'search_query': search_query,
    })


@login_required
def client_inventory_create_view(request):
    tenant = request.tenant
    form = ClientInventoryItemForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.tenant = tenant
        item.created_by = request.user
        item.save()
        messages.success(request, f'Inventory item {item.tracking_number} created successfully.')
        return redirect('tpl:client_inventory_detail', pk=item.pk)

    return render(request, 'tpl/client_inventory_form.html', {
        'form': form,
        'title': 'New Inventory Item',
    })


@login_required
def client_inventory_detail_view(request, pk):
    item = get_object_or_404(ClientInventoryItem, pk=pk, tenant=request.tenant)
    return render(request, 'tpl/client_inventory_detail.html', {'item': item})


@login_required
def client_inventory_edit_view(request, pk):
    tenant = request.tenant
    item = get_object_or_404(ClientInventoryItem, pk=pk, tenant=tenant)
    form = ClientInventoryItemForm(request.POST or None, instance=item, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Inventory item {item.tracking_number} updated successfully.')
        return redirect('tpl:client_inventory_detail', pk=item.pk)

    return render(request, 'tpl/client_inventory_form.html', {
        'form': form,
        'item': item,
        'title': 'Edit Inventory Item',
    })


@login_required
def client_inventory_delete_view(request, pk):
    item = get_object_or_404(ClientInventoryItem, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Inventory item deleted successfully.')
        return redirect('tpl:client_inventory_list')
    return redirect('tpl:client_inventory_list')


# =============================================================================
# SLA Views
# =============================================================================

@login_required
def sla_list_view(request):
    tenant = request.tenant
    slas = SLA.objects.filter(tenant=tenant).select_related('client', 'created_by')
    status_choices = SLA.STATUS_CHOICES
    clients = Client.objects.filter(tenant=tenant, status='active')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        slas = slas.filter(
            Q(sla_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        slas = slas.filter(status=status_filter)

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        slas = slas.filter(client_id=client_filter)

    return render(request, 'tpl/sla_list.html', {
        'slas': slas,
        'status_choices': status_choices,
        'clients': clients,
        'search_query': search_query,
    })


@login_required
def sla_create_view(request):
    tenant = request.tenant
    form = SLAForm(request.POST or None, tenant=tenant)
    formset = SLAMetricFormSet(request.POST or None, prefix='metrics')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        sla = form.save(commit=False)
        sla.tenant = tenant
        sla.created_by = request.user
        sla.save()
        formset.instance = sla
        formset.save()
        messages.success(request, f'SLA {sla.sla_number} created successfully.')
        return redirect('tpl:sla_detail', pk=sla.pk)

    return render(request, 'tpl/sla_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New SLA',
    })


@login_required
def sla_detail_view(request, pk):
    sla = get_object_or_404(SLA, pk=pk, tenant=request.tenant)
    metrics = sla.metrics.all()
    return render(request, 'tpl/sla_detail.html', {
        'sla': sla,
        'metrics': metrics,
    })


@login_required
def sla_edit_view(request, pk):
    tenant = request.tenant
    sla = get_object_or_404(SLA, pk=pk, tenant=tenant, status='draft')
    form = SLAForm(request.POST or None, instance=sla, tenant=tenant)
    formset = SLAMetricFormSet(request.POST or None, instance=sla, prefix='metrics')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'SLA {sla.sla_number} updated successfully.')
        return redirect('tpl:sla_detail', pk=sla.pk)

    return render(request, 'tpl/sla_form.html', {
        'form': form,
        'formset': formset,
        'sla': sla,
        'title': 'Edit SLA',
    })


@login_required
def sla_delete_view(request, pk):
    sla = get_object_or_404(SLA, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        sla.delete()
        messages.success(request, 'SLA deleted successfully.')
        return redirect('tpl:sla_list')
    return redirect('tpl:sla_list')


@login_required
def sla_activate_view(request, pk):
    sla = get_object_or_404(SLA, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        sla.status = 'active'
        sla.save()
        messages.success(request, f'SLA {sla.sla_number} activated.')
    return redirect('tpl:sla_detail', pk=sla.pk)


@login_required
def sla_breached_view(request, pk):
    sla = get_object_or_404(SLA, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        sla.status = 'breached'
        sla.save()
        messages.success(request, f'SLA {sla.sla_number} marked as breached.')
    return redirect('tpl:sla_detail', pk=sla.pk)


@login_required
def sla_expire_view(request, pk):
    sla = get_object_or_404(SLA, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and sla.status in ('active', 'breached'):
        sla.status = 'expired'
        sla.save()
        messages.success(request, f'SLA {sla.sla_number} marked as expired.')
    return redirect('tpl:sla_detail', pk=sla.pk)


# =============================================================================
# Integration Config Views
# =============================================================================

@login_required
def integration_list_view(request):
    tenant = request.tenant
    integrations = IntegrationConfig.objects.filter(tenant=tenant).select_related('client', 'created_by')
    status_choices = IntegrationConfig.STATUS_CHOICES
    clients = Client.objects.filter(tenant=tenant, status='active')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        integrations = integrations.filter(
            Q(config_number__icontains=search_query)
            | Q(integration_name__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        integrations = integrations.filter(status=status_filter)

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        integrations = integrations.filter(client_id=client_filter)

    return render(request, 'tpl/integration_list.html', {
        'integrations': integrations,
        'status_choices': status_choices,
        'clients': clients,
        'search_query': search_query,
    })


@login_required
def integration_create_view(request):
    tenant = request.tenant
    form = IntegrationConfigForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        config = form.save(commit=False)
        config.tenant = tenant
        config.created_by = request.user
        config.save()
        messages.success(request, f'Integration {config.config_number} created successfully.')
        return redirect('tpl:integration_detail', pk=config.pk)

    return render(request, 'tpl/integration_form.html', {
        'form': form,
        'title': 'New Integration',
    })


@login_required
def integration_detail_view(request, pk):
    config = get_object_or_404(IntegrationConfig, pk=pk, tenant=request.tenant)
    logs = config.logs.all()[:20]
    return render(request, 'tpl/integration_detail.html', {
        'config': config,
        'logs': logs,
    })


@login_required
def integration_edit_view(request, pk):
    tenant = request.tenant
    config = get_object_or_404(IntegrationConfig, pk=pk, tenant=tenant, status='draft')
    form = IntegrationConfigForm(request.POST or None, instance=config, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Integration {config.config_number} updated successfully.')
        return redirect('tpl:integration_detail', pk=config.pk)

    return render(request, 'tpl/integration_form.html', {
        'form': form,
        'config': config,
        'title': 'Edit Integration',
    })


@login_required
def integration_delete_view(request, pk):
    config = get_object_or_404(IntegrationConfig, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Integration deleted successfully.')
        return redirect('tpl:integration_list')
    return redirect('tpl:integration_list')


@login_required
def integration_activate_view(request, pk):
    config = get_object_or_404(IntegrationConfig, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        config.status = 'active'
        config.save()
        messages.success(request, f'Integration {config.config_number} activated.')
    return redirect('tpl:integration_detail', pk=config.pk)


@login_required
def integration_pause_view(request, pk):
    config = get_object_or_404(IntegrationConfig, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        config.status = 'paused'
        config.save()
        messages.success(request, f'Integration {config.config_number} paused.')
    return redirect('tpl:integration_detail', pk=config.pk)


@login_required
def integration_disable_view(request, pk):
    config = get_object_or_404(IntegrationConfig, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and config.status in ('active', 'paused', 'error'):
        config.status = 'disabled'
        config.save()
        messages.success(request, f'Integration {config.config_number} disabled.')
    return redirect('tpl:integration_detail', pk=config.pk)


# =============================================================================
# Rental Agreement Views
# =============================================================================

@login_required
def rental_list_view(request):
    tenant = request.tenant
    rentals = RentalAgreement.objects.filter(tenant=tenant).select_related('client', 'warehouse', 'created_by')
    status_choices = RentalAgreement.STATUS_CHOICES
    clients = Client.objects.filter(tenant=tenant, status='active')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rentals = rentals.filter(
            Q(agreement_number__icontains=search_query)
            | Q(client__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        rentals = rentals.filter(status=status_filter)

    client_filter = request.GET.get('client', '').strip()
    if client_filter:
        rentals = rentals.filter(client_id=client_filter)

    return render(request, 'tpl/rental_list.html', {
        'rentals': rentals,
        'status_choices': status_choices,
        'clients': clients,
        'search_query': search_query,
    })


@login_required
def rental_create_view(request):
    tenant = request.tenant
    form = RentalAgreementForm(request.POST or None, tenant=tenant)
    formset = SpaceUsageRecordFormSet(request.POST or None, prefix='usage')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        rental = form.save(commit=False)
        rental.tenant = tenant
        rental.created_by = request.user
        rental.save()
        formset.instance = rental
        formset.save()
        messages.success(request, f'Rental agreement {rental.agreement_number} created successfully.')
        return redirect('tpl:rental_detail', pk=rental.pk)

    return render(request, 'tpl/rental_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Rental Agreement',
    })


@login_required
def rental_detail_view(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk, tenant=request.tenant)
    usage_records = rental.usage_records.all()
    return render(request, 'tpl/rental_detail.html', {
        'rental': rental,
        'usage_records': usage_records,
    })


@login_required
def rental_edit_view(request, pk):
    tenant = request.tenant
    rental = get_object_or_404(RentalAgreement, pk=pk, tenant=tenant, status='draft')
    form = RentalAgreementForm(request.POST or None, instance=rental, tenant=tenant)
    formset = SpaceUsageRecordFormSet(request.POST or None, instance=rental, prefix='usage')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Rental agreement {rental.agreement_number} updated successfully.')
        return redirect('tpl:rental_detail', pk=rental.pk)

    return render(request, 'tpl/rental_form.html', {
        'form': form,
        'formset': formset,
        'rental': rental,
        'title': 'Edit Rental Agreement',
    })


@login_required
def rental_delete_view(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        rental.delete()
        messages.success(request, 'Rental agreement deleted successfully.')
        return redirect('tpl:rental_list')
    return redirect('tpl:rental_list')


@login_required
def rental_activate_view(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        rental.status = 'active'
        rental.save()
        messages.success(request, f'Rental agreement {rental.agreement_number} activated.')
    return redirect('tpl:rental_detail', pk=rental.pk)


@login_required
def rental_expire_view(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        rental.status = 'expired'
        rental.save()
        messages.success(request, f'Rental agreement {rental.agreement_number} marked as expired.')
    return redirect('tpl:rental_detail', pk=rental.pk)


@login_required
def rental_terminate_view(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk, tenant=request.tenant)
    if request.method == 'POST' and rental.status in ('active', 'expired'):
        rental.status = 'terminated'
        rental.save()
        messages.success(request, f'Rental agreement {rental.agreement_number} terminated.')
    return redirect('tpl:rental_detail', pk=rental.pk)
