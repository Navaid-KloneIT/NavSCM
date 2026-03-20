from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    GoodsReceiptNoteForm,
    GRNItemFormSet,
    ItemCategoryForm,
    ItemForm,
    PurchaseOrderForm,
    PurchaseOrderItemFormSet,
    PurchaseRequisitionForm,
    PurchaseRequisitionItemFormSet,
    RFQForm,
    RFQItemFormSet,
    VendorForm,
    VendorInvoiceForm,
    VendorInvoiceItemFormSet,
)
from .models import (
    GoodsReceiptNote,
    Item,
    ItemCategory,
    PurchaseOrder,
    PurchaseRequisition,
    RFQ,
    RFQVendor,
    ThreeWayMatch,
    Vendor,
    VendorInvoice,
    VendorQuote,
)


# =============================================================================
# ITEM CATEGORY VIEWS
# =============================================================================

@login_required
def category_list_view(request):
    tenant = request.tenant
    categories = ItemCategory.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        categories = categories.filter(is_active=True)
    elif status_filter == 'inactive':
        categories = categories.filter(is_active=False)

    return render(request, 'procurement/category_list.html', {
        'categories': categories,
        'search_query': search_query,
    })


@login_required
def category_create_view(request):
    tenant = request.tenant
    form = ItemCategoryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.tenant = tenant
        from django.utils.text import slugify
        category.slug = slugify(category.name)
        # Ensure unique slug
        base_slug = category.slug
        counter = 1
        while ItemCategory.objects.filter(tenant=tenant, slug=category.slug).exists():
            category.slug = f"{base_slug}-{counter}"
            counter += 1
        category.save()
        messages.success(request, f'Category "{category.name}" created successfully.')
        return redirect('procurement:category_list')

    return render(request, 'procurement/category_form.html', {
        'form': form,
        'title': 'Add Category',
    })


@login_required
def category_edit_view(request, pk):
    tenant = request.tenant
    category = get_object_or_404(ItemCategory, pk=pk, tenant=tenant)
    form = ItemCategoryForm(request.POST or None, instance=category)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Category "{category.name}" updated successfully.')
        return redirect('procurement:category_list')

    return render(request, 'procurement/category_form.html', {
        'form': form,
        'title': 'Edit Category',
        'category': category,
    })


# =============================================================================
# ITEM VIEWS
# =============================================================================

@login_required
def item_list_view(request):
    tenant = request.tenant
    items = Item.objects.filter(tenant=tenant).select_related('category')
    categories = ItemCategory.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query)
            | Q(code__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        items = items.filter(category_id=category_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        items = items.filter(is_active=True)
    elif status_filter == 'inactive':
        items = items.filter(is_active=False)

    return render(request, 'procurement/item_list.html', {
        'items': items,
        'categories': categories,
        'search_query': search_query,
    })


@login_required
def item_create_view(request):
    tenant = request.tenant
    form = ItemForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.tenant = tenant
        item.save()
        messages.success(request, f'Item "{item.name}" created successfully.')
        return redirect('procurement:item_list')

    return render(request, 'procurement/item_form.html', {
        'form': form,
        'title': 'Add Item',
    })


@login_required
def item_edit_view(request, pk):
    tenant = request.tenant
    item = get_object_or_404(Item, pk=pk, tenant=tenant)
    form = ItemForm(request.POST or None, instance=item, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Item "{item.name}" updated successfully.')
        return redirect('procurement:item_list')

    return render(request, 'procurement/item_form.html', {
        'form': form,
        'title': 'Edit Item',
        'item': item,
    })


# =============================================================================
# VENDOR VIEWS
# =============================================================================

@login_required
def vendor_list_view(request):
    tenant = request.tenant
    vendors = Vendor.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        vendors = vendors.filter(
            Q(name__icontains=search_query)
            | Q(code__icontains=search_query)
            | Q(contact_person__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        vendors = vendors.filter(is_active=True)
    elif status_filter == 'inactive':
        vendors = vendors.filter(is_active=False)

    return render(request, 'procurement/vendor_list.html', {
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def vendor_create_view(request):
    tenant = request.tenant
    form = VendorForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        vendor = form.save(commit=False)
        vendor.tenant = tenant
        vendor.created_by = request.user
        vendor.save()
        messages.success(request, f'Vendor "{vendor.name}" created successfully.')
        return redirect('procurement:vendor_list')

    return render(request, 'procurement/vendor_form.html', {
        'form': form,
        'title': 'Add Vendor',
    })


@login_required
def vendor_edit_view(request, pk):
    tenant = request.tenant
    vendor = get_object_or_404(Vendor, pk=pk, tenant=tenant)
    form = VendorForm(request.POST or None, instance=vendor)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Vendor "{vendor.name}" updated successfully.')
        return redirect('procurement:vendor_list')

    return render(request, 'procurement/vendor_form.html', {
        'form': form,
        'title': 'Edit Vendor',
        'vendor': vendor,
    })


@login_required
def vendor_detail_view(request, pk):
    tenant = request.tenant
    vendor = get_object_or_404(Vendor, pk=pk, tenant=tenant)
    purchase_orders = PurchaseOrder.objects.filter(
        tenant=tenant, vendor=vendor
    ).order_by('-created_at')[:10]

    return render(request, 'procurement/vendor_detail.html', {
        'vendor': vendor,
        'purchase_orders': purchase_orders,
    })


# =============================================================================
# PURCHASE REQUISITION VIEWS
# =============================================================================

@login_required
def requisition_list_view(request):
    tenant = request.tenant
    requisitions = PurchaseRequisition.objects.filter(tenant=tenant).select_related('requested_by')
    status_choices = PurchaseRequisition.STATUS_CHOICES
    priority_choices = PurchaseRequisition.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        requisitions = requisitions.filter(
            Q(requisition_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(department__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        requisitions = requisitions.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        requisitions = requisitions.filter(priority=priority_filter)

    return render(request, 'procurement/requisition_list.html', {
        'requisitions': requisitions,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def requisition_create_view(request):
    tenant = request.tenant
    form = PurchaseRequisitionForm(request.POST or None)
    formset = PurchaseRequisitionItemFormSet(
        request.POST or None,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        requisition = form.save(commit=False)
        requisition.tenant = tenant
        requisition.requested_by = request.user
        requisition.save()
        formset.instance = requisition
        formset.save()
        messages.success(request, f'Requisition {requisition.requisition_number} created successfully.')
        return redirect('procurement:requisition_detail', pk=requisition.pk)

    return render(request, 'procurement/requisition_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Purchase Requisition',
    })


@login_required
def requisition_edit_view(request, pk):
    tenant = request.tenant
    requisition = get_object_or_404(PurchaseRequisition, pk=pk, tenant=tenant)

    if requisition.status not in ('draft', 'rejected'):
        messages.error(request, 'Only draft or rejected requisitions can be edited.')
        return redirect('procurement:requisition_detail', pk=pk)

    form = PurchaseRequisitionForm(request.POST or None, instance=requisition)
    formset = PurchaseRequisitionItemFormSet(
        request.POST or None,
        instance=requisition,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Requisition {requisition.requisition_number} updated successfully.')
        return redirect('procurement:requisition_detail', pk=requisition.pk)

    return render(request, 'procurement/requisition_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Requisition {requisition.requisition_number}',
        'requisition': requisition,
    })


@login_required
def requisition_detail_view(request, pk):
    tenant = request.tenant
    requisition = get_object_or_404(
        PurchaseRequisition.objects.select_related('requested_by', 'approved_by'),
        pk=pk,
        tenant=tenant,
    )
    items = requisition.items.select_related('item').all()

    return render(request, 'procurement/requisition_detail.html', {
        'requisition': requisition,
        'items': items,
    })


@login_required
def requisition_submit_view(request, pk):
    tenant = request.tenant
    requisition = get_object_or_404(PurchaseRequisition, pk=pk, tenant=tenant)

    if request.method == 'POST' and requisition.status in ('draft', 'rejected'):
        requisition.status = 'pending_approval'
        requisition.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Requisition {requisition.requisition_number} submitted for approval.')

    return redirect('procurement:requisition_detail', pk=pk)


@login_required
def requisition_approve_view(request, pk):
    tenant = request.tenant
    requisition = get_object_or_404(PurchaseRequisition, pk=pk, tenant=tenant)

    if request.method == 'POST' and requisition.status == 'pending_approval':
        action = request.POST.get('action')
        if action == 'approve':
            requisition.status = 'approved'
            requisition.approved_by = request.user
            requisition.approved_at = timezone.now()
            requisition.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
            messages.success(request, f'Requisition {requisition.requisition_number} approved.')
        elif action == 'reject':
            requisition.status = 'rejected'
            requisition.save(update_fields=['status', 'updated_at'])
            messages.warning(request, f'Requisition {requisition.requisition_number} rejected.')

    return redirect('procurement:requisition_detail', pk=pk)


# =============================================================================
# RFQ VIEWS
# =============================================================================

@login_required
def rfq_list_view(request):
    tenant = request.tenant
    rfqs = RFQ.objects.filter(tenant=tenant).select_related('created_by', 'requisition')
    status_choices = RFQ.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rfqs = rfqs.filter(
            Q(rfq_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        rfqs = rfqs.filter(status=status_filter)

    return render(request, 'procurement/rfq_list.html', {
        'rfqs': rfqs,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def rfq_create_view(request):
    tenant = request.tenant
    form = RFQForm(request.POST or None, tenant=tenant)
    formset = RFQItemFormSet(
        request.POST or None,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        rfq = form.save(commit=False)
        rfq.tenant = tenant
        rfq.created_by = request.user
        rfq.save()
        formset.instance = rfq
        formset.save()
        # Create RFQVendor entries for selected vendors
        selected_vendors = form.cleaned_data.get('vendors', [])
        for vendor in selected_vendors:
            RFQVendor.objects.create(rfq=rfq, vendor=vendor)
        messages.success(request, f'RFQ {rfq.rfq_number} created successfully.')
        return redirect('procurement:rfq_detail', pk=rfq.pk)

    return render(request, 'procurement/rfq_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create RFQ',
    })


@login_required
def rfq_edit_view(request, pk):
    tenant = request.tenant
    rfq = get_object_or_404(RFQ, pk=pk, tenant=tenant)

    if rfq.status not in ('draft',):
        messages.error(request, 'Only draft RFQs can be edited.')
        return redirect('procurement:rfq_detail', pk=pk)

    form = RFQForm(request.POST or None, instance=rfq, tenant=tenant)
    formset = RFQItemFormSet(
        request.POST or None,
        instance=rfq,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        # Update vendor selections
        selected_vendors = form.cleaned_data.get('vendors', [])
        rfq.rfq_vendors.exclude(vendor__in=selected_vendors).delete()
        for vendor in selected_vendors:
            RFQVendor.objects.get_or_create(rfq=rfq, vendor=vendor)
        messages.success(request, f'RFQ {rfq.rfq_number} updated successfully.')
        return redirect('procurement:rfq_detail', pk=rfq.pk)

    # Pre-select existing vendors
    form.fields['vendors'].initial = rfq.rfq_vendors.values_list('vendor_id', flat=True)

    return render(request, 'procurement/rfq_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit RFQ {rfq.rfq_number}',
        'rfq': rfq,
    })


@login_required
def rfq_detail_view(request, pk):
    tenant = request.tenant
    rfq = get_object_or_404(
        RFQ.objects.select_related('created_by', 'requisition'),
        pk=pk,
        tenant=tenant,
    )
    items = rfq.items.select_related('item').all()
    rfq_vendors = rfq.rfq_vendors.select_related('vendor').all()

    # Build quote comparison matrix
    quote_matrix = []
    for rfq_item in items:
        row = {
            'item': rfq_item,
            'quotes': [],
        }
        for rfq_vendor in rfq_vendors:
            quote = VendorQuote.objects.filter(
                rfq_vendor=rfq_vendor, rfq_item=rfq_item
            ).first()
            row['quotes'].append(quote)
        quote_matrix.append(row)

    return render(request, 'procurement/rfq_detail.html', {
        'rfq': rfq,
        'items': items,
        'rfq_vendors': rfq_vendors,
        'quote_matrix': quote_matrix,
    })


# =============================================================================
# PURCHASE ORDER VIEWS
# =============================================================================

@login_required
def po_list_view(request):
    tenant = request.tenant
    purchase_orders = PurchaseOrder.objects.filter(
        tenant=tenant
    ).select_related('vendor', 'created_by')
    status_choices = PurchaseOrder.STATUS_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        purchase_orders = purchase_orders.filter(
            Q(po_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        purchase_orders = purchase_orders.filter(status=status_filter)

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        purchase_orders = purchase_orders.filter(vendor_id=vendor_filter)

    return render(request, 'procurement/po_list.html', {
        'purchase_orders': purchase_orders,
        'status_choices': status_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def po_create_view(request):
    tenant = request.tenant
    form = PurchaseOrderForm(request.POST or None, tenant=tenant)
    formset = PurchaseOrderItemFormSet(
        request.POST or None,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        po = form.save(commit=False)
        po.tenant = tenant
        po.created_by = request.user
        po.save()
        formset.instance = po
        formset.save()
        po.calculate_totals()
        messages.success(request, f'Purchase Order {po.po_number} created successfully.')
        return redirect('procurement:po_detail', pk=po.pk)

    return render(request, 'procurement/po_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Purchase Order',
    })


@login_required
def po_edit_view(request, pk):
    tenant = request.tenant
    po = get_object_or_404(PurchaseOrder, pk=pk, tenant=tenant)

    if po.status not in ('draft',):
        messages.error(request, 'Only draft purchase orders can be edited.')
        return redirect('procurement:po_detail', pk=pk)

    form = PurchaseOrderForm(request.POST or None, instance=po, tenant=tenant)
    formset = PurchaseOrderItemFormSet(
        request.POST or None,
        instance=po,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        po.calculate_totals()
        messages.success(request, f'Purchase Order {po.po_number} updated successfully.')
        return redirect('procurement:po_detail', pk=po.pk)

    return render(request, 'procurement/po_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Purchase Order {po.po_number}',
        'po': po,
    })


@login_required
def po_detail_view(request, pk):
    tenant = request.tenant
    po = get_object_or_404(
        PurchaseOrder.objects.select_related('vendor', 'created_by', 'approved_by', 'rfq', 'requisition'),
        pk=pk,
        tenant=tenant,
    )
    items = po.items.select_related('item').all()
    grns = po.grns.all()
    shipment_updates = po.shipment_updates.all()

    return render(request, 'procurement/po_detail.html', {
        'po': po,
        'items': items,
        'grns': grns,
        'shipment_updates': shipment_updates,
    })


@login_required
def po_submit_view(request, pk):
    tenant = request.tenant
    po = get_object_or_404(PurchaseOrder, pk=pk, tenant=tenant)

    if request.method == 'POST' and po.status == 'draft':
        po.status = 'pending_approval'
        po.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Purchase Order {po.po_number} submitted for approval.')

    return redirect('procurement:po_detail', pk=pk)


@login_required
def po_approve_view(request, pk):
    tenant = request.tenant
    po = get_object_or_404(PurchaseOrder, pk=pk, tenant=tenant)

    if request.method == 'POST' and po.status == 'pending_approval':
        action = request.POST.get('action')
        if action == 'approve':
            po.status = 'approved'
            po.approved_by = request.user
            po.approved_at = timezone.now()
            po.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
            messages.success(request, f'Purchase Order {po.po_number} approved.')
        elif action == 'reject':
            po.status = 'draft'
            po.save(update_fields=['status', 'updated_at'])
            messages.warning(request, f'Purchase Order {po.po_number} rejected and returned to draft.')

    return redirect('procurement:po_detail', pk=pk)


@login_required
def po_cancel_view(request, pk):
    tenant = request.tenant
    po = get_object_or_404(PurchaseOrder, pk=pk, tenant=tenant)

    if request.method == 'POST' and po.status not in ('received', 'cancelled'):
        po.status = 'cancelled'
        po.save(update_fields=['status', 'updated_at'])
        messages.warning(request, f'Purchase Order {po.po_number} cancelled.')

    return redirect('procurement:po_detail', pk=pk)


# =============================================================================
# GOODS RECEIPT NOTE (GRN) VIEWS
# =============================================================================

@login_required
def grn_list_view(request):
    tenant = request.tenant
    grns = GoodsReceiptNote.objects.filter(
        tenant=tenant
    ).select_related('purchase_order', 'received_by')
    status_choices = GoodsReceiptNote.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        grns = grns.filter(
            Q(grn_number__icontains=search_query)
            | Q(purchase_order__po_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        grns = grns.filter(status=status_filter)

    return render(request, 'procurement/grn_list.html', {
        'grns': grns,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def grn_create_view(request):
    tenant = request.tenant
    form = GoodsReceiptNoteForm(request.POST or None, tenant=tenant)
    formset = GRNItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        grn = form.save(commit=False)
        grn.tenant = tenant
        grn.received_by = request.user
        grn.save()
        formset.instance = grn
        formset.save()
        # Update PO item received quantities
        for grn_item in grn.items.all():
            po_item = grn_item.po_item
            po_item.received_quantity = (po_item.received_quantity or 0) + grn_item.accepted_quantity
            po_item.save(update_fields=['received_quantity'])
        messages.success(request, f'GRN {grn.grn_number} created successfully.')
        return redirect('procurement:grn_detail', pk=grn.pk)

    return render(request, 'procurement/grn_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Goods Receipt Note',
    })


@login_required
def grn_detail_view(request, pk):
    tenant = request.tenant
    grn = get_object_or_404(
        GoodsReceiptNote.objects.select_related('purchase_order', 'received_by'),
        pk=pk,
        tenant=tenant,
    )
    items = grn.items.select_related('po_item', 'po_item__item').all()

    return render(request, 'procurement/grn_detail.html', {
        'grn': grn,
        'items': items,
    })


# =============================================================================
# VENDOR INVOICE VIEWS
# =============================================================================

@login_required
def invoice_list_view(request):
    tenant = request.tenant
    invoices = VendorInvoice.objects.filter(
        tenant=tenant
    ).select_related('vendor', 'purchase_order')
    status_choices = VendorInvoice.STATUS_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        invoices = invoices.filter(vendor_id=vendor_filter)

    return render(request, 'procurement/invoice_list.html', {
        'invoices': invoices,
        'status_choices': status_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def invoice_create_view(request):
    tenant = request.tenant
    form = VendorInvoiceForm(request.POST or None, tenant=tenant)
    formset = VendorInvoiceItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        invoice = form.save(commit=False)
        invoice.tenant = tenant
        invoice.save()
        formset.instance = invoice
        formset.save()
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
        return redirect('procurement:invoice_detail', pk=invoice.pk)

    return render(request, 'procurement/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Vendor Invoice',
    })


@login_required
def invoice_detail_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(
        VendorInvoice.objects.select_related('vendor', 'purchase_order', 'grn'),
        pk=pk,
        tenant=tenant,
    )
    items = invoice.items.select_related('po_item', 'po_item__item').all()
    matches = invoice.matches.all()

    return render(request, 'procurement/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'matches': matches,
    })


# =============================================================================
# 3-WAY MATCH / RECONCILIATION VIEWS
# =============================================================================

@login_required
def reconciliation_view(request):
    tenant = request.tenant
    matches = ThreeWayMatch.objects.filter(
        tenant=tenant
    ).select_related('invoice', 'purchase_order', 'grn')

    status_choices = ThreeWayMatch.MATCH_STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        matches = matches.filter(
            Q(invoice__invoice_number__icontains=search_query)
            | Q(purchase_order__po_number__icontains=search_query)
            | Q(grn__grn_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        matches = matches.filter(match_status=status_filter)

    # Summary stats
    stats = {
        'total': matches.count(),
        'full_match': matches.filter(match_status='full_match').count(),
        'partial_match': matches.filter(match_status='partial_match').count(),
        'mismatch': matches.filter(match_status='mismatch').count(),
    }

    return render(request, 'procurement/reconciliation.html', {
        'matches': matches,
        'status_choices': status_choices,
        'stats': stats,
        'search_query': search_query,
    })


@login_required
def reconciliation_create_view(request):
    tenant = request.tenant

    if request.method == 'POST':
        invoice_id = request.POST.get('invoice')
        po_id = request.POST.get('purchase_order')
        grn_id = request.POST.get('grn')

        invoice = get_object_or_404(VendorInvoice, pk=invoice_id, tenant=tenant)
        po = get_object_or_404(PurchaseOrder, pk=po_id, tenant=tenant)
        grn = get_object_or_404(GoodsReceiptNote, pk=grn_id, tenant=tenant)

        # Perform matching logic
        po_total = po.total_amount
        grn_qty_total = sum(item.accepted_quantity for item in grn.items.all())
        po_qty_total = sum(item.quantity for item in po.items.all())
        inv_total = invoice.total_amount

        qty_match = grn_qty_total == po_qty_total
        price_match = inv_total == po_total
        total_match = qty_match and price_match

        if total_match:
            match_status = 'full_match'
        elif qty_match or price_match:
            match_status = 'partial_match'
        else:
            match_status = 'mismatch'

        match = ThreeWayMatch.objects.create(
            tenant=tenant,
            invoice=invoice,
            purchase_order=po,
            grn=grn,
            match_status=match_status,
            quantity_match=qty_match,
            price_match=price_match,
            total_match=total_match,
        )

        # Update invoice status
        if match_status == 'full_match':
            invoice.status = 'matched'
        elif match_status == 'partial_match':
            invoice.status = 'partially_matched'
        else:
            invoice.status = 'disputed'
        invoice.save(update_fields=['status'])

        messages.success(request, f'Three-way match completed: {match.get_match_status_display()}')
        return redirect('procurement:reconciliation')

    # GET: show form to select invoice, PO, GRN
    invoices = VendorInvoice.objects.filter(tenant=tenant, status='pending')
    purchase_orders = PurchaseOrder.objects.filter(tenant=tenant)
    grns = GoodsReceiptNote.objects.filter(tenant=tenant)

    return render(request, 'procurement/reconciliation_form.html', {
        'invoices': invoices,
        'purchase_orders': purchase_orders,
        'grns': grns,
        'title': 'Create Three-Way Match',
    })
