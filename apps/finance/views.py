from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    APInvoiceForm, APInvoiceItemFormSet, APPaymentForm,
    ARInvoiceForm, ARInvoiceItemFormSet, ARPaymentForm,
    BudgetForm, BudgetEntryFormSet,
    LandedCostSheetForm, LandedCostComponentFormSet,
    TaxRateForm, TaxTransactionForm,
)
from .models import (
    APInvoice, APPayment, ARInvoice, ARPayment,
    Budget, LandedCostSheet, TaxRate, TaxTransaction,
)


# =============================================================================
# AP INVOICE VIEWS
# =============================================================================

@login_required
def ap_invoice_list_view(request):
    tenant = request.tenant
    invoices = APInvoice.objects.filter(tenant=tenant).select_related(
        'vendor', 'created_by'
    )
    status_choices = APInvoice.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    return render(request, 'finance/ap_invoice_list.html', {
        'invoices': invoices,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def ap_invoice_create_view(request):
    tenant = request.tenant
    form = APInvoiceForm(request.POST or None, tenant=tenant)
    formset = APInvoiceItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        invoice = form.save(commit=False)
        invoice.tenant = tenant
        invoice.created_by = request.user
        invoice.save()
        formset.instance = invoice
        formset.save()
        messages.success(request, f'AP Invoice {invoice.invoice_number} created successfully.')
        return redirect('finance:ap_invoice_detail', pk=invoice.pk)

    return render(request, 'finance/ap_invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create AP Invoice',
    })


@login_required
def ap_invoice_detail_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(APInvoice, pk=pk, tenant=tenant)
    line_items = invoice.items.all()
    payments = invoice.payments.all()

    return render(request, 'finance/ap_invoice_detail.html', {
        'invoice': invoice,
        'line_items': line_items,
        'payments': payments,
    })


@login_required
def ap_invoice_edit_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(APInvoice, pk=pk, tenant=tenant)

    if invoice.status != 'draft':
        messages.error(request, 'Only draft invoices can be edited.')
        return redirect('finance:ap_invoice_detail', pk=pk)

    form = APInvoiceForm(request.POST or None, instance=invoice, tenant=tenant)
    formset = APInvoiceItemFormSet(request.POST or None, prefix='items', instance=invoice)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'AP Invoice {invoice.invoice_number} updated successfully.')
        return redirect('finance:ap_invoice_detail', pk=invoice.pk)

    return render(request, 'finance/ap_invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit AP Invoice',
        'invoice': invoice,
    })


@login_required
def ap_invoice_delete_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(APInvoice, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if invoice.status != 'draft':
            messages.error(request, 'Only draft invoices can be deleted.')
            return redirect('finance:ap_invoice_detail', pk=pk)
        number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'AP Invoice {number} deleted successfully.')
        return redirect('finance:ap_invoice_list')
    return redirect('finance:ap_invoice_list')


@login_required
def ap_invoice_approve_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(APInvoice, pk=pk, tenant=tenant)

    if request.method == 'POST' and invoice.status in ('draft', 'pending_approval'):
        invoice.status = 'approved'
        invoice.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'AP Invoice {invoice.invoice_number} approved.')

    return redirect('finance:ap_invoice_detail', pk=pk)


@login_required
def ap_invoice_overdue_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(APInvoice, pk=pk, tenant=tenant)

    if request.method == 'POST' and invoice.status in ('approved', 'partially_paid'):
        invoice.status = 'overdue'
        invoice.save(update_fields=['status', 'updated_at'])
        messages.warning(request, f'AP Invoice {invoice.invoice_number} marked as overdue.')

    return redirect('finance:ap_invoice_detail', pk=pk)


@login_required
def ap_invoice_cancel_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(APInvoice, pk=pk, tenant=tenant)

    if request.method == 'POST' and invoice.status in ('draft', 'pending_approval', 'approved', 'overdue'):
        invoice.status = 'cancelled'
        invoice.save(update_fields=['status', 'updated_at'])
        messages.warning(request, f'AP Invoice {invoice.invoice_number} cancelled.')

    return redirect('finance:ap_invoice_detail', pk=pk)


# =============================================================================
# AP PAYMENT VIEWS
# =============================================================================

@login_required
def ap_payment_list_view(request):
    tenant = request.tenant
    payments = APPayment.objects.filter(tenant=tenant).select_related(
        'invoice', 'invoice__vendor', 'created_by'
    )

    search_query = request.GET.get('q', '').strip()
    if search_query:
        payments = payments.filter(
            Q(payment_number__icontains=search_query)
            | Q(reference_number__icontains=search_query)
            | Q(invoice__invoice_number__icontains=search_query)
        )

    return render(request, 'finance/ap_payment_list.html', {
        'payments': payments,
        'search_query': search_query,
    })


@login_required
def ap_payment_create_view(request):
    tenant = request.tenant
    form = APPaymentForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.tenant = tenant
        payment.created_by = request.user
        payment.save()
        messages.success(request, f'AP Payment {payment.payment_number} created successfully.')
        return redirect('finance:ap_payment_detail', pk=payment.pk)

    return render(request, 'finance/ap_payment_form.html', {
        'form': form,
        'title': 'Create AP Payment',
    })


@login_required
def ap_payment_detail_view(request, pk):
    tenant = request.tenant
    payment = get_object_or_404(APPayment, pk=pk, tenant=tenant)

    return render(request, 'finance/ap_payment_detail.html', {
        'payment': payment,
    })


@login_required
def ap_payment_delete_view(request, pk):
    tenant = request.tenant
    payment = get_object_or_404(APPayment, pk=pk, tenant=tenant)
    if request.method == 'POST':
        invoice = payment.invoice
        number = payment.payment_number
        payment.delete()
        # Recalculate invoice amount_paid and status
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
        invoice.amount_paid = total_paid
        if total_paid <= 0:
            if invoice.status in ('partially_paid', 'paid'):
                invoice.status = 'approved'
        elif total_paid < invoice.total_amount:
            invoice.status = 'partially_paid'
        else:
            invoice.status = 'paid'
        invoice.save(update_fields=['amount_paid', 'status', 'updated_at'])
        messages.success(request, f'AP Payment {number} deleted successfully.')
        return redirect('finance:ap_payment_list')
    return redirect('finance:ap_payment_list')


# =============================================================================
# AR INVOICE VIEWS
# =============================================================================

@login_required
def ar_invoice_list_view(request):
    tenant = request.tenant
    invoices = ARInvoice.objects.filter(tenant=tenant).select_related(
        'customer', 'created_by'
    )
    status_choices = ARInvoice.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query)
            | Q(customer__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    return render(request, 'finance/ar_invoice_list.html', {
        'invoices': invoices,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def ar_invoice_create_view(request):
    tenant = request.tenant
    form = ARInvoiceForm(request.POST or None, tenant=tenant)
    formset = ARInvoiceItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        invoice = form.save(commit=False)
        invoice.tenant = tenant
        invoice.created_by = request.user
        invoice.save()
        formset.instance = invoice
        formset.save()
        messages.success(request, f'AR Invoice {invoice.invoice_number} created successfully.')
        return redirect('finance:ar_invoice_detail', pk=invoice.pk)

    return render(request, 'finance/ar_invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create AR Invoice',
    })


@login_required
def ar_invoice_detail_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(ARInvoice, pk=pk, tenant=tenant)
    line_items = invoice.items.all()
    payments = invoice.payments.all()

    return render(request, 'finance/ar_invoice_detail.html', {
        'invoice': invoice,
        'line_items': line_items,
        'payments': payments,
    })


@login_required
def ar_invoice_edit_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(ARInvoice, pk=pk, tenant=tenant)

    if invoice.status != 'draft':
        messages.error(request, 'Only draft invoices can be edited.')
        return redirect('finance:ar_invoice_detail', pk=pk)

    form = ARInvoiceForm(request.POST or None, instance=invoice, tenant=tenant)
    formset = ARInvoiceItemFormSet(request.POST or None, prefix='items', instance=invoice)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'AR Invoice {invoice.invoice_number} updated successfully.')
        return redirect('finance:ar_invoice_detail', pk=invoice.pk)

    return render(request, 'finance/ar_invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit AR Invoice',
        'invoice': invoice,
    })


@login_required
def ar_invoice_delete_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(ARInvoice, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if invoice.status != 'draft':
            messages.error(request, 'Only draft invoices can be deleted.')
            return redirect('finance:ar_invoice_detail', pk=pk)
        number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'AR Invoice {number} deleted successfully.')
        return redirect('finance:ar_invoice_list')
    return redirect('finance:ar_invoice_list')


@login_required
def ar_invoice_send_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(ARInvoice, pk=pk, tenant=tenant)

    if request.method == 'POST' and invoice.status == 'draft':
        invoice.status = 'sent'
        invoice.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'AR Invoice {invoice.invoice_number} sent.')

    return redirect('finance:ar_invoice_detail', pk=pk)


@login_required
def ar_invoice_overdue_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(ARInvoice, pk=pk, tenant=tenant)

    if request.method == 'POST' and invoice.status in ('sent', 'partially_paid'):
        invoice.status = 'overdue'
        invoice.save(update_fields=['status', 'updated_at'])
        messages.warning(request, f'AR Invoice {invoice.invoice_number} marked as overdue.')

    return redirect('finance:ar_invoice_detail', pk=pk)


@login_required
def ar_invoice_cancel_view(request, pk):
    tenant = request.tenant
    invoice = get_object_or_404(ARInvoice, pk=pk, tenant=tenant)

    if request.method == 'POST' and invoice.status in ('draft', 'sent', 'overdue'):
        invoice.status = 'cancelled'
        invoice.save(update_fields=['status', 'updated_at'])
        messages.warning(request, f'AR Invoice {invoice.invoice_number} cancelled.')

    return redirect('finance:ar_invoice_detail', pk=pk)


# =============================================================================
# AR PAYMENT VIEWS
# =============================================================================

@login_required
def ar_payment_list_view(request):
    tenant = request.tenant
    payments = ARPayment.objects.filter(tenant=tenant).select_related(
        'invoice', 'invoice__customer', 'created_by'
    )

    search_query = request.GET.get('q', '').strip()
    if search_query:
        payments = payments.filter(
            Q(payment_number__icontains=search_query)
            | Q(reference_number__icontains=search_query)
            | Q(invoice__invoice_number__icontains=search_query)
        )

    return render(request, 'finance/ar_payment_list.html', {
        'payments': payments,
        'search_query': search_query,
    })


@login_required
def ar_payment_create_view(request):
    tenant = request.tenant
    form = ARPaymentForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.tenant = tenant
        payment.created_by = request.user
        payment.save()
        messages.success(request, f'AR Payment {payment.payment_number} created successfully.')
        return redirect('finance:ar_payment_detail', pk=payment.pk)

    return render(request, 'finance/ar_payment_form.html', {
        'form': form,
        'title': 'Create AR Payment',
    })


@login_required
def ar_payment_detail_view(request, pk):
    tenant = request.tenant
    payment = get_object_or_404(ARPayment, pk=pk, tenant=tenant)

    return render(request, 'finance/ar_payment_detail.html', {
        'payment': payment,
    })


@login_required
def ar_payment_delete_view(request, pk):
    tenant = request.tenant
    payment = get_object_or_404(ARPayment, pk=pk, tenant=tenant)
    if request.method == 'POST':
        invoice = payment.invoice
        number = payment.payment_number
        payment.delete()
        # Recalculate invoice amount_paid and status
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
        invoice.amount_paid = total_paid
        if total_paid <= 0:
            if invoice.status in ('partially_paid', 'paid'):
                invoice.status = 'sent'
        elif total_paid < invoice.total_amount:
            invoice.status = 'partially_paid'
        else:
            invoice.status = 'paid'
        invoice.save(update_fields=['amount_paid', 'status', 'updated_at'])
        messages.success(request, f'AR Payment {number} deleted successfully.')
        return redirect('finance:ar_payment_list')
    return redirect('finance:ar_payment_list')


# =============================================================================
# LANDED COST VIEWS
# =============================================================================

@login_required
def landed_cost_list_view(request):
    tenant = request.tenant
    sheets = LandedCostSheet.objects.filter(tenant=tenant).select_related(
        'shipment', 'purchase_order', 'carrier', 'created_by'
    )
    status_choices = LandedCostSheet.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        sheets = sheets.filter(
            Q(sheet_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        sheets = sheets.filter(status=status_filter)

    return render(request, 'finance/landed_cost_list.html', {
        'sheets': sheets,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def landed_cost_create_view(request):
    tenant = request.tenant
    form = LandedCostSheetForm(request.POST or None, tenant=tenant)
    formset = LandedCostComponentFormSet(request.POST or None, prefix='components')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        sheet = form.save(commit=False)
        sheet.tenant = tenant
        sheet.created_by = request.user
        sheet.save()
        formset.instance = sheet
        formset.save()
        messages.success(request, f'Landed Cost Sheet {sheet.sheet_number} created successfully.')
        return redirect('finance:landed_cost_detail', pk=sheet.pk)

    return render(request, 'finance/landed_cost_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Landed Cost Sheet',
    })


@login_required
def landed_cost_detail_view(request, pk):
    tenant = request.tenant
    sheet = get_object_or_404(LandedCostSheet, pk=pk, tenant=tenant)
    components = sheet.components.all()

    return render(request, 'finance/landed_cost_detail.html', {
        'sheet': sheet,
        'components': components,
    })


@login_required
def landed_cost_edit_view(request, pk):
    tenant = request.tenant
    sheet = get_object_or_404(LandedCostSheet, pk=pk, tenant=tenant)

    if sheet.status != 'draft':
        messages.error(request, 'Only draft landed cost sheets can be edited.')
        return redirect('finance:landed_cost_detail', pk=pk)

    form = LandedCostSheetForm(request.POST or None, instance=sheet, tenant=tenant)
    formset = LandedCostComponentFormSet(request.POST or None, prefix='components', instance=sheet)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Landed Cost Sheet {sheet.sheet_number} updated successfully.')
        return redirect('finance:landed_cost_detail', pk=sheet.pk)

    return render(request, 'finance/landed_cost_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Landed Cost Sheet',
        'sheet': sheet,
    })


@login_required
def landed_cost_delete_view(request, pk):
    tenant = request.tenant
    sheet = get_object_or_404(LandedCostSheet, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if sheet.status != 'draft':
            messages.error(request, 'Only draft landed cost sheets can be deleted.')
            return redirect('finance:landed_cost_detail', pk=pk)
        number = sheet.sheet_number
        sheet.delete()
        messages.success(request, f'Landed Cost Sheet {number} deleted successfully.')
        return redirect('finance:landed_cost_list')
    return redirect('finance:landed_cost_list')


@login_required
def landed_cost_calculate_view(request, pk):
    tenant = request.tenant
    sheet = get_object_or_404(LandedCostSheet, pk=pk, tenant=tenant)

    if request.method == 'POST' and sheet.status == 'draft':
        components_total = sheet.components.aggregate(total=Sum('amount'))['total'] or 0
        sheet.total_landed_cost = sheet.total_goods_cost + components_total
        sheet.status = 'calculated'
        sheet.save(update_fields=['total_landed_cost', 'status', 'updated_at'])
        messages.success(request, f'Landed Cost Sheet {sheet.sheet_number} calculated successfully.')

    return redirect('finance:landed_cost_detail', pk=pk)


@login_required
def landed_cost_finalize_view(request, pk):
    tenant = request.tenant
    sheet = get_object_or_404(LandedCostSheet, pk=pk, tenant=tenant)

    if request.method == 'POST' and sheet.status == 'calculated':
        sheet.status = 'finalized'
        sheet.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Landed Cost Sheet {sheet.sheet_number} finalized.')

    return redirect('finance:landed_cost_detail', pk=pk)


# =============================================================================
# BUDGET VIEWS
# =============================================================================

@login_required
def budget_list_view(request):
    tenant = request.tenant
    budgets = Budget.objects.filter(tenant=tenant)
    status_choices = Budget.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        budgets = budgets.filter(
            Q(budget_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(department__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        budgets = budgets.filter(status=status_filter)

    return render(request, 'finance/budget_list.html', {
        'budgets': budgets,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def budget_create_view(request):
    tenant = request.tenant
    form = BudgetForm(request.POST or None)
    formset = BudgetEntryFormSet(request.POST or None, prefix='entries')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        budget = form.save(commit=False)
        budget.tenant = tenant
        budget.created_by = request.user
        budget.save()
        formset.instance = budget
        formset.save()
        messages.success(request, f'Budget {budget.budget_number} created successfully.')
        return redirect('finance:budget_detail', pk=budget.pk)

    return render(request, 'finance/budget_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Budget',
    })


@login_required
def budget_detail_view(request, pk):
    tenant = request.tenant
    budget = get_object_or_404(Budget, pk=pk, tenant=tenant)
    entries = budget.entries.all()

    return render(request, 'finance/budget_detail.html', {
        'budget': budget,
        'entries': entries,
    })


@login_required
def budget_edit_view(request, pk):
    tenant = request.tenant
    budget = get_object_or_404(Budget, pk=pk, tenant=tenant)

    if budget.status != 'draft':
        messages.error(request, 'Only draft budgets can be edited.')
        return redirect('finance:budget_detail', pk=pk)

    form = BudgetForm(request.POST or None, instance=budget)
    formset = BudgetEntryFormSet(request.POST or None, prefix='entries', instance=budget)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Budget {budget.budget_number} updated successfully.')
        return redirect('finance:budget_detail', pk=budget.pk)

    return render(request, 'finance/budget_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Budget',
        'budget': budget,
    })


@login_required
def budget_delete_view(request, pk):
    tenant = request.tenant
    budget = get_object_or_404(Budget, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if budget.status != 'draft':
            messages.error(request, 'Only draft budgets can be deleted.')
            return redirect('finance:budget_detail', pk=pk)
        number = budget.budget_number
        budget.delete()
        messages.success(request, f'Budget {number} deleted successfully.')
        return redirect('finance:budget_list')
    return redirect('finance:budget_list')


@login_required
def budget_activate_view(request, pk):
    tenant = request.tenant
    budget = get_object_or_404(Budget, pk=pk, tenant=tenant)

    if request.method == 'POST' and budget.status == 'draft':
        budget.status = 'active'
        budget.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Budget {budget.budget_number} activated.')

    return redirect('finance:budget_detail', pk=pk)


@login_required
def budget_close_view(request, pk):
    tenant = request.tenant
    budget = get_object_or_404(Budget, pk=pk, tenant=tenant)

    if request.method == 'POST' and budget.status == 'active':
        budget.status = 'closed'
        budget.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Budget {budget.budget_number} closed.')

    return redirect('finance:budget_detail', pk=pk)


# =============================================================================
# TAX RATE VIEWS
# =============================================================================

@login_required
def tax_rate_list_view(request):
    tenant = request.tenant
    rates = TaxRate.objects.filter(tenant=tenant)
    tax_type_choices = TaxRate.TAX_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rates = rates.filter(
            Q(code__icontains=search_query)
            | Q(name__icontains=search_query)
        )

    tax_type_filter = request.GET.get('tax_type', '').strip()
    if tax_type_filter:
        rates = rates.filter(tax_type=tax_type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        rates = rates.filter(is_active=True)
    elif status_filter == 'inactive':
        rates = rates.filter(is_active=False)

    return render(request, 'finance/tax_rate_list.html', {
        'rates': rates,
        'tax_type_choices': tax_type_choices,
        'search_query': search_query,
    })


@login_required
def tax_rate_create_view(request):
    tenant = request.tenant
    form = TaxRateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        rate = form.save(commit=False)
        rate.tenant = tenant
        rate.save()
        messages.success(request, f'Tax Rate "{rate.name}" created successfully.')
        return redirect('finance:tax_rate_detail', pk=rate.pk)

    return render(request, 'finance/tax_rate_form.html', {
        'form': form,
        'title': 'Create Tax Rate',
    })


@login_required
def tax_rate_detail_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(TaxRate, pk=pk, tenant=tenant)
    transactions = rate.transactions.all()[:10]

    return render(request, 'finance/tax_rate_detail.html', {
        'rate': rate,
        'transactions': transactions,
    })


@login_required
def tax_rate_edit_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(TaxRate, pk=pk, tenant=tenant)
    form = TaxRateForm(request.POST or None, instance=rate)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Tax Rate "{rate.name}" updated successfully.')
        return redirect('finance:tax_rate_detail', pk=rate.pk)

    return render(request, 'finance/tax_rate_form.html', {
        'form': form,
        'title': 'Edit Tax Rate',
        'rate': rate,
    })


@login_required
def tax_rate_delete_view(request, pk):
    tenant = request.tenant
    rate = get_object_or_404(TaxRate, pk=pk, tenant=tenant)
    if request.method == 'POST':
        name = rate.name
        rate.delete()
        messages.success(request, f'Tax Rate "{name}" deleted successfully.')
        return redirect('finance:tax_rate_list')
    return redirect('finance:tax_rate_list')


# =============================================================================
# TAX TRANSACTION VIEWS
# =============================================================================

@login_required
def tax_transaction_list_view(request):
    tenant = request.tenant
    transactions = TaxTransaction.objects.filter(tenant=tenant).select_related(
        'tax_rate', 'created_by'
    )
    transaction_type_choices = TaxTransaction.TRANSACTION_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(transaction_number__icontains=search_query)
            | Q(reference_number__icontains=search_query)
        )

    type_filter = request.GET.get('transaction_type', '').strip()
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    return render(request, 'finance/tax_transaction_list.html', {
        'transactions': transactions,
        'transaction_type_choices': transaction_type_choices,
        'search_query': search_query,
    })


@login_required
def tax_transaction_create_view(request):
    tenant = request.tenant
    form = TaxTransactionForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        transaction = form.save(commit=False)
        transaction.tenant = tenant
        transaction.created_by = request.user
        transaction.save()
        messages.success(request, f'Tax Transaction {transaction.transaction_number} created successfully.')
        return redirect('finance:tax_transaction_detail', pk=transaction.pk)

    return render(request, 'finance/tax_transaction_form.html', {
        'form': form,
        'title': 'Create Tax Transaction',
    })


@login_required
def tax_transaction_detail_view(request, pk):
    tenant = request.tenant
    transaction = get_object_or_404(TaxTransaction, pk=pk, tenant=tenant)

    return render(request, 'finance/tax_transaction_detail.html', {
        'transaction': transaction,
    })
