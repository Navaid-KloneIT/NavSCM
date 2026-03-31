from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CatalogItemForm,
    OrderTrackingForm,
    PortalAccountForm,
    PortalDocumentForm,
    SupportTicketForm,
    TicketMessageFormSet,
    TrackingEventFormSet,
)
from .models import (
    CatalogItem,
    OrderTracking,
    PortalAccount,
    PortalDocument,
    SupportTicket,
)


# =============================================================================
# PORTAL ACCOUNT VIEWS
# =============================================================================

@login_required
def account_list_view(request):
    tenant = request.tenant
    accounts = PortalAccount.objects.filter(tenant=tenant).select_related(
        'customer', 'created_by',
    )
    status_choices = PortalAccount.STATUS_CHOICES
    payment_choices = PortalAccount.PAYMENT_METHOD_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        accounts = accounts.filter(
            Q(account_number__icontains=search_query)
            | Q(display_name__icontains=search_query)
            | Q(portal_email__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        accounts = accounts.filter(status=status_filter)

    payment_filter = request.GET.get('payment_method', '').strip()
    if payment_filter:
        accounts = accounts.filter(payment_method=payment_filter)

    return render(request, 'portal/account_list.html', {
        'accounts': accounts,
        'status_choices': status_choices,
        'payment_choices': payment_choices,
        'search_query': search_query,
    })


@login_required
def account_create_view(request):
    tenant = request.tenant
    form = PortalAccountForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        account = form.save(commit=False)
        account.tenant = tenant
        account.created_by = request.user
        account.save()
        messages.success(request, f'Portal Account {account.account_number} created successfully.')
        return redirect('portal:account_detail', pk=account.pk)

    return render(request, 'portal/account_form.html', {
        'form': form,
        'title': 'New Portal Account',
    })


@login_required
def account_detail_view(request, pk):
    account = get_object_or_404(PortalAccount, pk=pk, tenant=request.tenant)
    trackings = account.order_trackings.all()[:5]
    tickets = account.support_tickets.all()[:5]
    documents = account.portal_documents.all()[:5]

    return render(request, 'portal/account_detail.html', {
        'account': account,
        'trackings': trackings,
        'tickets': tickets,
        'documents': documents,
    })


@login_required
def account_edit_view(request, pk):
    tenant = request.tenant
    account = get_object_or_404(PortalAccount, pk=pk, tenant=tenant, status='pending')
    form = PortalAccountForm(request.POST or None, instance=account, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Portal Account {account.account_number} updated successfully.')
        return redirect('portal:account_detail', pk=account.pk)

    return render(request, 'portal/account_form.html', {
        'form': form,
        'account': account,
        'title': 'Edit Portal Account',
    })


@login_required
def account_delete_view(request, pk):
    account = get_object_or_404(PortalAccount, pk=pk, tenant=request.tenant, status='pending')
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Portal Account deleted successfully.')
        return redirect('portal:account_list')
    return redirect('portal:account_list')


@login_required
def account_activate_view(request, pk):
    account = get_object_or_404(PortalAccount, pk=pk, tenant=request.tenant)
    if account.status not in ('pending', 'suspended'):
        return redirect('portal:account_detail', pk=account.pk)
    if request.method == 'POST':
        account.status = 'active'
        account.save()
        messages.success(request, f'Portal Account {account.account_number} activated.')
    return redirect('portal:account_detail', pk=account.pk)


@login_required
def account_suspend_view(request, pk):
    account = get_object_or_404(PortalAccount, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        account.status = 'suspended'
        account.save()
        messages.warning(request, f'Portal Account {account.account_number} suspended.')
    return redirect('portal:account_detail', pk=account.pk)


@login_required
def account_close_view(request, pk):
    account = get_object_or_404(PortalAccount, pk=pk, tenant=request.tenant)
    if account.status == 'closed':
        return redirect('portal:account_detail', pk=account.pk)
    if request.method == 'POST':
        account.status = 'closed'
        account.save()
        messages.warning(request, f'Portal Account {account.account_number} closed.')
    return redirect('portal:account_detail', pk=account.pk)


# =============================================================================
# ORDER TRACKING VIEWS
# =============================================================================

@login_required
def tracking_list_view(request):
    tenant = request.tenant
    trackings = OrderTracking.objects.filter(tenant=tenant).select_related(
        'portal_account', 'order', 'shipment', 'created_by',
    )
    status_choices = OrderTracking.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        trackings = trackings.filter(
            Q(tracking_number__icontains=search_query)
            | Q(carrier_name__icontains=search_query)
            | Q(order__order_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        trackings = trackings.filter(current_status=status_filter)

    return render(request, 'portal/tracking_list.html', {
        'trackings': trackings,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def tracking_create_view(request):
    tenant = request.tenant
    form = OrderTrackingForm(request.POST or None, tenant=tenant)
    formset = TrackingEventFormSet(request.POST or None, prefix='events')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        tracking = form.save(commit=False)
        tracking.tenant = tenant
        tracking.created_by = request.user
        tracking.save()
        formset.instance = tracking
        formset.save()
        messages.success(request, f'Order Tracking {tracking.tracking_number} created successfully.')
        return redirect('portal:tracking_detail', pk=tracking.pk)

    return render(request, 'portal/tracking_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Order Tracking',
    })


@login_required
def tracking_detail_view(request, pk):
    tracking = get_object_or_404(OrderTracking, pk=pk, tenant=request.tenant)
    events = tracking.tracking_events.all()

    return render(request, 'portal/tracking_detail.html', {
        'tracking': tracking,
        'events': events,
    })


@login_required
def tracking_edit_view(request, pk):
    tenant = request.tenant
    tracking = get_object_or_404(OrderTracking, pk=pk, tenant=tenant, current_status='processing')
    form = OrderTrackingForm(request.POST or None, instance=tracking, tenant=tenant)
    formset = TrackingEventFormSet(
        request.POST or None, instance=tracking, prefix='events',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Order Tracking {tracking.tracking_number} updated successfully.')
        return redirect('portal:tracking_detail', pk=tracking.pk)

    return render(request, 'portal/tracking_form.html', {
        'form': form,
        'formset': formset,
        'tracking': tracking,
        'title': 'Edit Order Tracking',
    })


@login_required
def tracking_delete_view(request, pk):
    tracking = get_object_or_404(
        OrderTracking, pk=pk, tenant=request.tenant, current_status='processing',
    )
    if request.method == 'POST':
        tracking.delete()
        messages.success(request, 'Order Tracking deleted successfully.')
        return redirect('portal:tracking_list')
    return redirect('portal:tracking_list')


@login_required
def tracking_ship_view(request, pk):
    tracking = get_object_or_404(
        OrderTracking, pk=pk, tenant=request.tenant, current_status='processing',
    )
    if request.method == 'POST':
        tracking.current_status = 'shipped'
        tracking.save()
        messages.success(request, f'Tracking {tracking.tracking_number} marked as shipped.')
    return redirect('portal:tracking_detail', pk=tracking.pk)


@login_required
def tracking_deliver_view(request, pk):
    tracking = get_object_or_404(OrderTracking, pk=pk, tenant=request.tenant)
    if tracking.current_status not in ('shipped', 'in_transit', 'out_for_delivery'):
        return redirect('portal:tracking_detail', pk=tracking.pk)
    if request.method == 'POST':
        tracking.current_status = 'delivered'
        tracking.actual_delivery = timezone.now().date()
        tracking.save()
        messages.success(request, f'Tracking {tracking.tracking_number} delivered.')
    return redirect('portal:tracking_detail', pk=tracking.pk)


@login_required
def tracking_delay_view(request, pk):
    tracking = get_object_or_404(OrderTracking, pk=pk, tenant=request.tenant)
    if tracking.current_status in ('delivered', 'returned', 'cancelled'):
        return redirect('portal:tracking_detail', pk=tracking.pk)
    if request.method == 'POST':
        tracking.current_status = 'delayed'
        tracking.save()
        messages.warning(request, f'Tracking {tracking.tracking_number} marked as delayed.')
    return redirect('portal:tracking_detail', pk=tracking.pk)


@login_required
def tracking_cancel_view(request, pk):
    tracking = get_object_or_404(OrderTracking, pk=pk, tenant=request.tenant)
    if tracking.current_status in ('delivered', 'cancelled'):
        return redirect('portal:tracking_detail', pk=tracking.pk)
    if request.method == 'POST':
        tracking.current_status = 'cancelled'
        tracking.save()
        messages.warning(request, f'Tracking {tracking.tracking_number} cancelled.')
    return redirect('portal:tracking_detail', pk=tracking.pk)


# =============================================================================
# PORTAL DOCUMENT VIEWS
# =============================================================================

@login_required
def document_list_view(request):
    tenant = request.tenant
    documents = PortalDocument.objects.filter(tenant=tenant).select_related(
        'portal_account', 'order', 'uploaded_by',
    )
    status_choices = PortalDocument.STATUS_CHOICES
    type_choices = PortalDocument.DOCUMENT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        documents = documents.filter(
            Q(document_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(reference_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        documents = documents.filter(status=status_filter)

    type_filter = request.GET.get('document_type', '').strip()
    if type_filter:
        documents = documents.filter(document_type=type_filter)

    return render(request, 'portal/document_list.html', {
        'documents': documents,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def document_create_view(request):
    tenant = request.tenant
    form = PortalDocumentForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.tenant = tenant
        doc.uploaded_by = request.user
        doc.save()
        messages.success(request, f'Document {doc.document_number} created successfully.')
        return redirect('portal:document_detail', pk=doc.pk)

    return render(request, 'portal/document_form.html', {
        'form': form,
        'title': 'New Document',
    })


@login_required
def document_detail_view(request, pk):
    doc = get_object_or_404(PortalDocument, pk=pk, tenant=request.tenant)

    return render(request, 'portal/document_detail.html', {
        'doc': doc,
    })


@login_required
def document_edit_view(request, pk):
    tenant = request.tenant
    doc = get_object_or_404(PortalDocument, pk=pk, tenant=tenant, status='draft')
    form = PortalDocumentForm(request.POST or None, instance=doc, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Document {doc.document_number} updated successfully.')
        return redirect('portal:document_detail', pk=doc.pk)

    return render(request, 'portal/document_form.html', {
        'form': form,
        'doc': doc,
        'title': 'Edit Document',
    })


@login_required
def document_delete_view(request, pk):
    doc = get_object_or_404(PortalDocument, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Document deleted successfully.')
        return redirect('portal:document_list')
    return redirect('portal:document_list')


@login_required
def document_publish_view(request, pk):
    doc = get_object_or_404(PortalDocument, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        doc.status = 'published'
        doc.save()
        messages.success(request, f'Document {doc.document_number} published.')
    return redirect('portal:document_detail', pk=doc.pk)


@login_required
def document_archive_view(request, pk):
    doc = get_object_or_404(PortalDocument, pk=pk, tenant=request.tenant, status='published')
    if request.method == 'POST':
        doc.status = 'archived'
        doc.save()
        messages.info(request, f'Document {doc.document_number} archived.')
    return redirect('portal:document_detail', pk=doc.pk)


# =============================================================================
# SUPPORT TICKET VIEWS
# =============================================================================

@login_required
def ticket_list_view(request):
    tenant = request.tenant
    tickets = SupportTicket.objects.filter(tenant=tenant).select_related(
        'portal_account', 'order', 'assigned_to', 'created_by',
    )
    status_choices = SupportTicket.STATUS_CHOICES
    category_choices = SupportTicket.CATEGORY_CHOICES
    priority_choices = SupportTicket.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search_query)
            | Q(subject__icontains=search_query)
            | Q(portal_account__display_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        tickets = tickets.filter(category=category_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)

    return render(request, 'portal/ticket_list.html', {
        'tickets': tickets,
        'status_choices': status_choices,
        'category_choices': category_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def ticket_create_view(request):
    tenant = request.tenant
    form = SupportTicketForm(request.POST or None, tenant=tenant)
    formset = TicketMessageFormSet(request.POST or None, prefix='messages')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        ticket = form.save(commit=False)
        ticket.tenant = tenant
        ticket.created_by = request.user
        ticket.save()
        formset.instance = ticket
        formset.save()
        messages.success(request, f'Ticket {ticket.ticket_number} created successfully.')
        return redirect('portal:ticket_detail', pk=ticket.pk)

    return render(request, 'portal/ticket_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Support Ticket',
    })


@login_required
def ticket_detail_view(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=request.tenant)
    ticket_messages = ticket.messages.all()

    return render(request, 'portal/ticket_detail.html', {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
    })


@login_required
def ticket_edit_view(request, pk):
    tenant = request.tenant
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=tenant, status='open')
    form = SupportTicketForm(request.POST or None, instance=ticket, tenant=tenant)
    formset = TicketMessageFormSet(
        request.POST or None, instance=ticket, prefix='messages',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Ticket {ticket.ticket_number} updated successfully.')
        return redirect('portal:ticket_detail', pk=ticket.pk)

    return render(request, 'portal/ticket_form.html', {
        'form': form,
        'formset': formset,
        'ticket': ticket,
        'title': 'Edit Support Ticket',
    })


@login_required
def ticket_delete_view(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=request.tenant, status='open')
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Support Ticket deleted successfully.')
        return redirect('portal:ticket_list')
    return redirect('portal:ticket_list')


@login_required
def ticket_assign_view(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=request.tenant, status='open')
    if request.method == 'POST':
        ticket.status = 'in_progress'
        ticket.save()
        messages.success(request, f'Ticket {ticket.ticket_number} assigned.')
    return redirect('portal:ticket_detail', pk=ticket.pk)


@login_required
def ticket_progress_view(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=request.tenant)
    if ticket.status not in ('open', 'waiting_on_customer', 'reopened'):
        return redirect('portal:ticket_detail', pk=ticket.pk)
    if request.method == 'POST':
        ticket.status = 'in_progress'
        ticket.save()
        messages.success(request, f'Ticket {ticket.ticket_number} in progress.')
    return redirect('portal:ticket_detail', pk=ticket.pk)


@login_required
def ticket_resolve_view(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=request.tenant)
    if ticket.status in ('resolved', 'closed'):
        return redirect('portal:ticket_detail', pk=ticket.pk)
    if request.method == 'POST':
        ticket.status = 'resolved'
        ticket.resolved_at = timezone.now()
        ticket.save()
        messages.success(request, f'Ticket {ticket.ticket_number} resolved.')
    return redirect('portal:ticket_detail', pk=ticket.pk)


@login_required
def ticket_close_view(request, pk):
    ticket = get_object_or_404(
        SupportTicket, pk=pk, tenant=request.tenant, status='resolved',
    )
    if request.method == 'POST':
        ticket.status = 'closed'
        ticket.save()
        messages.info(request, f'Ticket {ticket.ticket_number} closed.')
    return redirect('portal:ticket_detail', pk=ticket.pk)


@login_required
def ticket_reopen_view(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, tenant=request.tenant)
    if ticket.status not in ('resolved', 'closed'):
        return redirect('portal:ticket_detail', pk=ticket.pk)
    if request.method == 'POST':
        ticket.status = 'reopened'
        ticket.resolved_at = None
        ticket.save()
        messages.warning(request, f'Ticket {ticket.ticket_number} reopened.')
    return redirect('portal:ticket_detail', pk=ticket.pk)


# =============================================================================
# CATALOG BROWSING VIEWS
# =============================================================================

@login_required
def catalog_list_view(request):
    tenant = request.tenant
    items = CatalogItem.objects.filter(tenant=tenant).select_related(
        'item', 'created_by',
    )
    stock_choices = CatalogItem.STOCK_STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        items = items.filter(
            Q(catalog_number__icontains=search_query)
            | Q(portal_name__icontains=search_query)
            | Q(category__icontains=search_query)
        )

    stock_filter = request.GET.get('stock_status', '').strip()
    if stock_filter:
        items = items.filter(stock_status=stock_filter)

    featured_filter = request.GET.get('featured', '').strip()
    if featured_filter == 'yes':
        items = items.filter(is_featured=True)
    elif featured_filter == 'no':
        items = items.filter(is_featured=False)

    active_filter = request.GET.get('active', '').strip()
    if active_filter == 'active':
        items = items.filter(is_active=True)
    elif active_filter == 'inactive':
        items = items.filter(is_active=False)

    return render(request, 'portal/catalog_list.html', {
        'items': items,
        'stock_choices': stock_choices,
        'search_query': search_query,
    })


@login_required
def catalog_create_view(request):
    tenant = request.tenant
    form = CatalogItemForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.tenant = tenant
        item.created_by = request.user
        item.save()
        messages.success(request, f'Catalog Item {item.catalog_number} created successfully.')
        return redirect('portal:catalog_detail', pk=item.pk)

    return render(request, 'portal/catalog_form.html', {
        'form': form,
        'title': 'New Catalog Item',
    })


@login_required
def catalog_detail_view(request, pk):
    item = get_object_or_404(CatalogItem, pk=pk, tenant=request.tenant)

    return render(request, 'portal/catalog_detail.html', {
        'item': item,
    })


@login_required
def catalog_edit_view(request, pk):
    tenant = request.tenant
    item = get_object_or_404(CatalogItem, pk=pk, tenant=tenant)
    form = CatalogItemForm(request.POST or None, instance=item, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Catalog Item {item.catalog_number} updated successfully.')
        return redirect('portal:catalog_detail', pk=item.pk)

    return render(request, 'portal/catalog_form.html', {
        'form': form,
        'item': item,
        'title': 'Edit Catalog Item',
    })


@login_required
def catalog_delete_view(request, pk):
    item = get_object_or_404(CatalogItem, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Catalog Item deleted successfully.')
        return redirect('portal:catalog_list')
    return redirect('portal:catalog_list')
