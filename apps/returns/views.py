from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    DispositionForm,
    RefundForm,
    ReturnAuthorizationForm,
    ReturnPortalSettingsForm,
    RMALineItemFormSet,
    WarrantyClaimForm,
    WarrantyClaimItemFormSet,
)
from .models import (
    Disposition,
    Refund,
    ReturnAuthorization,
    ReturnPortalSettings,
    WarrantyClaim,
)


# =============================================================================
# RETURN AUTHORIZATION (RMA) VIEWS
# =============================================================================

@login_required
def rma_list_view(request):
    tenant = request.tenant
    rmas = ReturnAuthorization.objects.filter(tenant=tenant).select_related(
        'customer', 'order', 'approved_by', 'created_by',
    )
    status_choices = ReturnAuthorization.STATUS_CHOICES
    type_choices = ReturnAuthorization.RETURN_TYPE_CHOICES
    reason_choices = ReturnAuthorization.REASON_CATEGORY_CHOICES
    priority_choices = ReturnAuthorization.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        rmas = rmas.filter(
            Q(rma_number__icontains=search_query)
            | Q(customer__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        rmas = rmas.filter(status=status_filter)

    type_filter = request.GET.get('return_type', '').strip()
    if type_filter:
        rmas = rmas.filter(return_type=type_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        rmas = rmas.filter(priority=priority_filter)

    return render(request, 'returns/rma_list.html', {
        'rmas': rmas,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'reason_choices': reason_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def rma_create_view(request):
    tenant = request.tenant
    form = ReturnAuthorizationForm(request.POST or None, tenant=tenant)
    formset = RMALineItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        rma = form.save(commit=False)
        rma.tenant = tenant
        rma.created_by = request.user
        rma.save()
        formset.instance = rma
        formset.save()
        messages.success(request, f'RMA {rma.rma_number} created successfully.')
        return redirect('returns:rma_detail', pk=rma.pk)

    return render(request, 'returns/rma_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Return Authorization',
    })


@login_required
def rma_detail_view(request, pk):
    tenant = request.tenant
    rma = get_object_or_404(ReturnAuthorization, pk=pk, tenant=tenant)
    line_items = rma.line_items.select_related('item')
    refunds = rma.refunds.all()
    dispositions = rma.dispositions.select_related('item')

    return render(request, 'returns/rma_detail.html', {
        'rma': rma,
        'line_items': line_items,
        'refunds': refunds,
        'dispositions': dispositions,
    })


@login_required
def rma_edit_view(request, pk):
    tenant = request.tenant
    rma = get_object_or_404(ReturnAuthorization, pk=pk, tenant=tenant, status='draft')
    form = ReturnAuthorizationForm(request.POST or None, instance=rma, tenant=tenant)
    formset = RMALineItemFormSet(
        request.POST or None, instance=rma, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'RMA {rma.rma_number} updated successfully.')
        return redirect('returns:rma_detail', pk=rma.pk)

    return render(request, 'returns/rma_form.html', {
        'form': form,
        'formset': formset,
        'rma': rma,
        'title': 'Edit Return Authorization',
    })


@login_required
def rma_delete_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        rma.delete()
        messages.success(request, 'RMA deleted successfully.')
        return redirect('returns:rma_list')
    return redirect('returns:rma_list')


@login_required
def rma_submit_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        rma.status = 'submitted'
        rma.save()
        messages.success(request, f'RMA {rma.rma_number} submitted.')
    return redirect('returns:rma_detail', pk=rma.pk)


@login_required
def rma_approve_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='submitted',
    )
    if request.method == 'POST':
        rma.status = 'approved'
        rma.approved_by = request.user
        rma.approved_date = timezone.now().date()
        rma.save()
        messages.success(request, f'RMA {rma.rma_number} approved.')
    return redirect('returns:rma_detail', pk=rma.pk)


@login_required
def rma_reject_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='submitted',
    )
    if request.method == 'POST':
        rma.status = 'rejected'
        rma.save()
        messages.success(request, f'RMA {rma.rma_number} rejected.')
    return redirect('returns:rma_detail', pk=rma.pk)


@login_required
def rma_receive_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        rma.status = 'receiving'
        rma.save()
        messages.success(request, f'RMA {rma.rma_number} moved to receiving.')
    return redirect('returns:rma_detail', pk=rma.pk)


@login_required
def rma_received_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='receiving',
    )
    if request.method == 'POST':
        rma.status = 'received'
        rma.save()
        messages.success(request, f'RMA {rma.rma_number} marked as received.')
    return redirect('returns:rma_detail', pk=rma.pk)


@login_required
def rma_close_view(request, pk):
    rma = get_object_or_404(
        ReturnAuthorization, pk=pk, tenant=request.tenant, status='received',
    )
    if request.method == 'POST':
        rma.status = 'closed'
        rma.save()
        messages.success(request, f'RMA {rma.rma_number} closed.')
    return redirect('returns:rma_detail', pk=rma.pk)


# =============================================================================
# REFUND VIEWS
# =============================================================================

@login_required
def refund_list_view(request):
    tenant = request.tenant
    refunds = Refund.objects.filter(tenant=tenant).select_related(
        'rma', 'rma__customer', 'approved_by', 'created_by',
    )
    status_choices = Refund.STATUS_CHOICES
    type_choices = Refund.REFUND_TYPE_CHOICES
    method_choices = Refund.REFUND_METHOD_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        refunds = refunds.filter(
            Q(refund_number__icontains=search_query)
            | Q(rma__rma_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        refunds = refunds.filter(status=status_filter)

    type_filter = request.GET.get('refund_type', '').strip()
    if type_filter:
        refunds = refunds.filter(refund_type=type_filter)

    method_filter = request.GET.get('refund_method', '').strip()
    if method_filter:
        refunds = refunds.filter(refund_method=method_filter)

    return render(request, 'returns/refund_list.html', {
        'refunds': refunds,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'method_choices': method_choices,
        'search_query': search_query,
    })


@login_required
def refund_create_view(request):
    tenant = request.tenant
    form = RefundForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        refund = form.save(commit=False)
        refund.tenant = tenant
        refund.created_by = request.user
        refund.save()
        messages.success(request, f'Refund {refund.refund_number} created successfully.')
        return redirect('returns:refund_detail', pk=refund.pk)

    return render(request, 'returns/refund_form.html', {
        'form': form,
        'title': 'New Refund',
    })


@login_required
def refund_detail_view(request, pk):
    tenant = request.tenant
    refund = get_object_or_404(Refund, pk=pk, tenant=tenant)

    return render(request, 'returns/refund_detail.html', {
        'refund': refund,
    })


@login_required
def refund_edit_view(request, pk):
    tenant = request.tenant
    refund = get_object_or_404(Refund, pk=pk, tenant=tenant, status='draft')
    form = RefundForm(request.POST or None, instance=refund, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Refund {refund.refund_number} updated successfully.')
        return redirect('returns:refund_detail', pk=refund.pk)

    return render(request, 'returns/refund_form.html', {
        'form': form,
        'refund': refund,
        'title': 'Edit Refund',
    })


@login_required
def refund_delete_view(request, pk):
    refund = get_object_or_404(
        Refund, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        refund.delete()
        messages.success(request, 'Refund deleted successfully.')
        return redirect('returns:refund_list')
    return redirect('returns:refund_list')


@login_required
def refund_submit_view(request, pk):
    refund = get_object_or_404(
        Refund, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        refund.status = 'pending_approval'
        refund.save()
        messages.success(request, f'Refund {refund.refund_number} submitted for approval.')
    return redirect('returns:refund_detail', pk=refund.pk)


@login_required
def refund_approve_view(request, pk):
    refund = get_object_or_404(
        Refund, pk=pk, tenant=request.tenant, status='pending_approval',
    )
    if request.method == 'POST':
        refund.status = 'approved'
        refund.approved_by = request.user
        refund.save()
        messages.success(request, f'Refund {refund.refund_number} approved.')
    return redirect('returns:refund_detail', pk=refund.pk)


@login_required
def refund_process_view(request, pk):
    refund = get_object_or_404(
        Refund, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        refund.status = 'processing'
        refund.save()
        messages.success(request, f'Refund {refund.refund_number} is now processing.')
    return redirect('returns:refund_detail', pk=refund.pk)


@login_required
def refund_complete_view(request, pk):
    refund = get_object_or_404(
        Refund, pk=pk, tenant=request.tenant, status='processing',
    )
    if request.method == 'POST':
        refund.status = 'completed'
        refund.processed_date = timezone.now().date()
        refund.save()
        messages.success(request, f'Refund {refund.refund_number} completed.')
    return redirect('returns:refund_detail', pk=refund.pk)


# =============================================================================
# DISPOSITION VIEWS
# =============================================================================

@login_required
def disposition_list_view(request):
    tenant = request.tenant
    dispositions = Disposition.objects.filter(tenant=tenant).select_related(
        'rma', 'item', 'assigned_to', 'created_by',
    )
    status_choices = Disposition.STATUS_CHOICES
    decision_choices = Disposition.DISPOSITION_DECISION_CHOICES
    condition_choices = Disposition.CONDITION_RECEIVED_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        dispositions = dispositions.filter(
            Q(disposition_number__icontains=search_query)
            | Q(item__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        dispositions = dispositions.filter(status=status_filter)

    decision_filter = request.GET.get('decision', '').strip()
    if decision_filter:
        dispositions = dispositions.filter(disposition_decision=decision_filter)

    condition_filter = request.GET.get('condition', '').strip()
    if condition_filter:
        dispositions = dispositions.filter(condition_received=condition_filter)

    return render(request, 'returns/disposition_list.html', {
        'dispositions': dispositions,
        'status_choices': status_choices,
        'decision_choices': decision_choices,
        'condition_choices': condition_choices,
        'search_query': search_query,
    })


@login_required
def disposition_create_view(request):
    tenant = request.tenant
    form = DispositionForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        disposition = form.save(commit=False)
        disposition.tenant = tenant
        disposition.created_by = request.user
        disposition.save()
        messages.success(request, f'Disposition {disposition.disposition_number} created successfully.')
        return redirect('returns:disposition_detail', pk=disposition.pk)

    return render(request, 'returns/disposition_form.html', {
        'form': form,
        'title': 'New Disposition',
    })


@login_required
def disposition_detail_view(request, pk):
    tenant = request.tenant
    disposition = get_object_or_404(Disposition, pk=pk, tenant=tenant)

    return render(request, 'returns/disposition_detail.html', {
        'disposition': disposition,
    })


@login_required
def disposition_edit_view(request, pk):
    tenant = request.tenant
    disposition = get_object_or_404(Disposition, pk=pk, tenant=tenant, status='pending')
    form = DispositionForm(request.POST or None, instance=disposition, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Disposition {disposition.disposition_number} updated successfully.')
        return redirect('returns:disposition_detail', pk=disposition.pk)

    return render(request, 'returns/disposition_form.html', {
        'form': form,
        'disposition': disposition,
        'title': 'Edit Disposition',
    })


@login_required
def disposition_delete_view(request, pk):
    disposition = get_object_or_404(
        Disposition, pk=pk, tenant=request.tenant, status='pending',
    )
    if request.method == 'POST':
        disposition.delete()
        messages.success(request, 'Disposition deleted successfully.')
        return redirect('returns:disposition_list')
    return redirect('returns:disposition_list')


@login_required
def disposition_inspect_view(request, pk):
    disposition = get_object_or_404(
        Disposition, pk=pk, tenant=request.tenant, status='pending',
    )
    if request.method == 'POST':
        disposition.status = 'inspecting'
        disposition.save()
        messages.success(request, f'Disposition {disposition.disposition_number} moved to inspection.')
    return redirect('returns:disposition_detail', pk=disposition.pk)


@login_required
def disposition_decide_view(request, pk):
    disposition = get_object_or_404(
        Disposition, pk=pk, tenant=request.tenant, status='inspecting',
    )
    if request.method == 'POST':
        disposition.status = 'decided'
        disposition.save()
        messages.success(request, f'Disposition {disposition.disposition_number} decision recorded.')
    return redirect('returns:disposition_detail', pk=disposition.pk)


@login_required
def disposition_process_view(request, pk):
    disposition = get_object_or_404(
        Disposition, pk=pk, tenant=request.tenant, status='decided',
    )
    if request.method == 'POST':
        disposition.status = 'processing'
        disposition.save()
        messages.success(request, f'Disposition {disposition.disposition_number} is now processing.')
    return redirect('returns:disposition_detail', pk=disposition.pk)


@login_required
def disposition_complete_view(request, pk):
    disposition = get_object_or_404(
        Disposition, pk=pk, tenant=request.tenant, status='processing',
    )
    if request.method == 'POST':
        disposition.status = 'completed'
        disposition.completed_date = timezone.now().date()
        disposition.save()
        messages.success(request, f'Disposition {disposition.disposition_number} completed.')
    return redirect('returns:disposition_detail', pk=disposition.pk)


# =============================================================================
# WARRANTY CLAIM VIEWS
# =============================================================================

@login_required
def warranty_list_view(request):
    tenant = request.tenant
    claims = WarrantyClaim.objects.filter(tenant=tenant).select_related(
        'vendor', 'item', 'rma', 'created_by',
    )
    status_choices = WarrantyClaim.STATUS_CHOICES
    type_choices = WarrantyClaim.CLAIM_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        claims = claims.filter(
            Q(claim_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        claims = claims.filter(status=status_filter)

    type_filter = request.GET.get('claim_type', '').strip()
    if type_filter:
        claims = claims.filter(claim_type=type_filter)

    return render(request, 'returns/warranty_list.html', {
        'claims': claims,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def warranty_create_view(request):
    tenant = request.tenant
    form = WarrantyClaimForm(request.POST or None, tenant=tenant)
    formset = WarrantyClaimItemFormSet(request.POST or None, prefix='claim_items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        claim = form.save(commit=False)
        claim.tenant = tenant
        claim.created_by = request.user
        claim.save()
        formset.instance = claim
        formset.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} created successfully.')
        return redirect('returns:warranty_detail', pk=claim.pk)

    return render(request, 'returns/warranty_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Warranty Claim',
    })


@login_required
def warranty_detail_view(request, pk):
    tenant = request.tenant
    claim = get_object_or_404(WarrantyClaim, pk=pk, tenant=tenant)
    claim_items = claim.claim_items.all()

    return render(request, 'returns/warranty_detail.html', {
        'claim': claim,
        'claim_items': claim_items,
    })


@login_required
def warranty_edit_view(request, pk):
    tenant = request.tenant
    claim = get_object_or_404(WarrantyClaim, pk=pk, tenant=tenant, status='draft')
    form = WarrantyClaimForm(request.POST or None, instance=claim, tenant=tenant)
    formset = WarrantyClaimItemFormSet(
        request.POST or None, instance=claim, prefix='claim_items',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} updated successfully.')
        return redirect('returns:warranty_detail', pk=claim.pk)

    return render(request, 'returns/warranty_form.html', {
        'form': form,
        'formset': formset,
        'claim': claim,
        'title': 'Edit Warranty Claim',
    })


@login_required
def warranty_delete_view(request, pk):
    claim = get_object_or_404(
        WarrantyClaim, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        claim.delete()
        messages.success(request, 'Warranty Claim deleted successfully.')
        return redirect('returns:warranty_list')
    return redirect('returns:warranty_list')


@login_required
def warranty_submit_view(request, pk):
    claim = get_object_or_404(
        WarrantyClaim, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        claim.status = 'submitted'
        claim.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} submitted.')
    return redirect('returns:warranty_detail', pk=claim.pk)


@login_required
def warranty_review_view(request, pk):
    claim = get_object_or_404(
        WarrantyClaim, pk=pk, tenant=request.tenant, status='submitted',
    )
    if request.method == 'POST':
        claim.status = 'under_review'
        claim.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} moved to review.')
    return redirect('returns:warranty_detail', pk=claim.pk)


@login_required
def warranty_approve_view(request, pk):
    claim = get_object_or_404(
        WarrantyClaim, pk=pk, tenant=request.tenant, status='under_review',
    )
    if request.method == 'POST':
        claim.status = 'approved'
        claim.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} approved.')
    return redirect('returns:warranty_detail', pk=claim.pk)


@login_required
def warranty_settle_view(request, pk):
    claim = get_object_or_404(
        WarrantyClaim, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        claim.status = 'settled'
        claim.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} settled.')
    return redirect('returns:warranty_detail', pk=claim.pk)


@login_required
def warranty_deny_view(request, pk):
    claim = get_object_or_404(
        WarrantyClaim, pk=pk, tenant=request.tenant, status='under_review',
    )
    if request.method == 'POST':
        claim.status = 'denied'
        claim.save()
        messages.warning(request, f'Warranty Claim {claim.claim_number} denied.')
    return redirect('returns:warranty_detail', pk=claim.pk)


@login_required
def warranty_close_view(request, pk):
    claim = get_object_or_404(WarrantyClaim, pk=pk, tenant=request.tenant)
    if claim.status not in ('settled', 'denied'):
        return redirect('returns:warranty_detail', pk=claim.pk)
    if request.method == 'POST':
        claim.status = 'closed'
        claim.save()
        messages.success(request, f'Warranty Claim {claim.claim_number} closed.')
    return redirect('returns:warranty_detail', pk=claim.pk)


# =============================================================================
# RETURN PORTAL SETTINGS VIEW
# =============================================================================

@login_required
def portal_settings_view(request):
    tenant = request.tenant
    settings_obj, _ = ReturnPortalSettings.objects.get_or_create(tenant=tenant)
    form = ReturnPortalSettingsForm(request.POST or None, instance=settings_obj)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Return Portal Settings updated successfully.')
        return redirect('returns:portal_settings')

    return render(request, 'returns/portal_settings.html', {
        'form': form,
        'settings_obj': settings_obj,
    })
