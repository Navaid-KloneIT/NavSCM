from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ComplianceCheckItemFormSet,
    ComplianceRecordForm,
    ContractDocumentFormSet,
    ContractForm,
    LicenseForm,
    SustainabilityMetricFormSet,
    SustainabilityReportForm,
    TradeDocumentForm,
    TradeDocumentItemFormSet,
)
from .models import (
    ComplianceRecord,
    Contract,
    License,
    SustainabilityReport,
    TradeDocument,
)


# =============================================================================
# CONTRACT REPOSITORY VIEWS
# =============================================================================

@login_required
def contract_list_view(request):
    tenant = request.tenant
    contracts = Contract.objects.filter(tenant=tenant).select_related(
        'vendor', 'created_by',
    )
    status_choices = Contract.STATUS_CHOICES
    type_choices = Contract.CONTRACT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        contracts = contracts.filter(
            Q(contract_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        contracts = contracts.filter(status=status_filter)

    type_filter = request.GET.get('contract_type', '').strip()
    if type_filter:
        contracts = contracts.filter(contract_type=type_filter)

    return render(request, 'contracts/contract_list.html', {
        'contracts': contracts,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def contract_create_view(request):
    tenant = request.tenant
    form = ContractForm(request.POST or None, tenant=tenant)
    formset = ContractDocumentFormSet(request.POST or None, prefix='documents')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        contract = form.save(commit=False)
        contract.tenant = tenant
        contract.created_by = request.user
        contract.save()
        formset.instance = contract
        formset.save()
        messages.success(request, f'Contract {contract.contract_number} created successfully.')
        return redirect('contracts:contract_detail', pk=contract.pk)

    return render(request, 'contracts/contract_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Contract',
    })


@login_required
def contract_detail_view(request, pk):
    tenant = request.tenant
    contract = get_object_or_404(Contract, pk=pk, tenant=tenant)
    documents = contract.documents.all()

    return render(request, 'contracts/contract_detail.html', {
        'contract': contract,
        'documents': documents,
    })


@login_required
def contract_edit_view(request, pk):
    tenant = request.tenant
    contract = get_object_or_404(Contract, pk=pk, tenant=tenant, status='draft')
    form = ContractForm(request.POST or None, instance=contract, tenant=tenant)
    formset = ContractDocumentFormSet(
        request.POST or None, instance=contract, prefix='documents',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Contract {contract.contract_number} updated successfully.')
        return redirect('contracts:contract_detail', pk=contract.pk)

    return render(request, 'contracts/contract_form.html', {
        'form': form,
        'formset': formset,
        'contract': contract,
        'title': 'Edit Contract',
    })


@login_required
def contract_delete_view(request, pk):
    contract = get_object_or_404(
        Contract, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contract deleted successfully.')
        return redirect('contracts:contract_list')
    return redirect('contracts:contract_list')


@login_required
def contract_activate_view(request, pk):
    contract = get_object_or_404(
        Contract, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        contract.status = 'active'
        contract.save()
        messages.success(request, f'Contract {contract.contract_number} activated.')
    return redirect('contracts:contract_detail', pk=contract.pk)


@login_required
def contract_review_view(request, pk):
    contract = get_object_or_404(
        Contract, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        contract.status = 'under_review'
        contract.save()
        messages.success(request, f'Contract {contract.contract_number} moved to review.')
    return redirect('contracts:contract_detail', pk=contract.pk)


@login_required
def contract_terminate_view(request, pk):
    contract = get_object_or_404(Contract, pk=pk, tenant=request.tenant)
    if contract.status not in ('active', 'under_review'):
        return redirect('contracts:contract_detail', pk=contract.pk)
    if request.method == 'POST':
        contract.status = 'terminated'
        contract.save()
        messages.warning(request, f'Contract {contract.contract_number} terminated.')
    return redirect('contracts:contract_detail', pk=contract.pk)


@login_required
def contract_expire_view(request, pk):
    contract = get_object_or_404(
        Contract, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        contract.status = 'expired'
        contract.save()
        messages.info(request, f'Contract {contract.contract_number} marked as expired.')
    return redirect('contracts:contract_detail', pk=contract.pk)


# =============================================================================
# COMPLIANCE TRACKING VIEWS
# =============================================================================

@login_required
def compliance_list_view(request):
    tenant = request.tenant
    records = ComplianceRecord.objects.filter(tenant=tenant).select_related(
        'responsible_person', 'created_by',
    )
    status_choices = ComplianceRecord.STATUS_CHOICES
    type_choices = ComplianceRecord.REGULATION_TYPE_CHOICES
    risk_choices = ComplianceRecord.RISK_LEVEL_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        records = records.filter(
            Q(compliance_number__icontains=search_query)
            | Q(regulation_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        records = records.filter(status=status_filter)

    type_filter = request.GET.get('regulation_type', '').strip()
    if type_filter:
        records = records.filter(regulation_type=type_filter)

    risk_filter = request.GET.get('risk_level', '').strip()
    if risk_filter:
        records = records.filter(risk_level=risk_filter)

    return render(request, 'contracts/compliance_list.html', {
        'records': records,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'risk_choices': risk_choices,
        'search_query': search_query,
    })


@login_required
def compliance_create_view(request):
    tenant = request.tenant
    form = ComplianceRecordForm(request.POST or None, tenant=tenant)
    formset = ComplianceCheckItemFormSet(request.POST or None, prefix='check_items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        record = form.save(commit=False)
        record.tenant = tenant
        record.created_by = request.user
        record.save()
        formset.instance = record
        formset.save()
        messages.success(request, f'Compliance Record {record.compliance_number} created successfully.')
        return redirect('contracts:compliance_detail', pk=record.pk)

    return render(request, 'contracts/compliance_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Compliance Record',
    })


@login_required
def compliance_detail_view(request, pk):
    tenant = request.tenant
    record = get_object_or_404(ComplianceRecord, pk=pk, tenant=tenant)
    check_items = record.check_items.all()

    return render(request, 'contracts/compliance_detail.html', {
        'record': record,
        'check_items': check_items,
    })


@login_required
def compliance_edit_view(request, pk):
    tenant = request.tenant
    record = get_object_or_404(ComplianceRecord, pk=pk, tenant=tenant, status='draft')
    form = ComplianceRecordForm(request.POST or None, instance=record, tenant=tenant)
    formset = ComplianceCheckItemFormSet(
        request.POST or None, instance=record, prefix='check_items',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Compliance Record {record.compliance_number} updated successfully.')
        return redirect('contracts:compliance_detail', pk=record.pk)

    return render(request, 'contracts/compliance_form.html', {
        'form': form,
        'formset': formset,
        'record': record,
        'title': 'Edit Compliance Record',
    })


@login_required
def compliance_delete_view(request, pk):
    record = get_object_or_404(
        ComplianceRecord, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Compliance Record deleted successfully.')
        return redirect('contracts:compliance_list')
    return redirect('contracts:compliance_list')


@login_required
def compliance_mark_compliant_view(request, pk):
    record = get_object_or_404(
        ComplianceRecord, pk=pk, tenant=request.tenant,
    )
    if record.status not in ('draft', 'under_review'):
        return redirect('contracts:compliance_detail', pk=record.pk)
    if request.method == 'POST':
        record.status = 'in_compliance'
        record.save()
        messages.success(request, f'Compliance Record {record.compliance_number} marked as compliant.')
    return redirect('contracts:compliance_detail', pk=record.pk)


@login_required
def compliance_mark_non_compliant_view(request, pk):
    record = get_object_or_404(
        ComplianceRecord, pk=pk, tenant=request.tenant,
    )
    if record.status not in ('draft', 'under_review', 'in_compliance'):
        return redirect('contracts:compliance_detail', pk=record.pk)
    if request.method == 'POST':
        record.status = 'non_compliant'
        record.save()
        messages.warning(request, f'Compliance Record {record.compliance_number} marked as non-compliant.')
    return redirect('contracts:compliance_detail', pk=record.pk)


@login_required
def compliance_review_view(request, pk):
    record = get_object_or_404(
        ComplianceRecord, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        record.status = 'under_review'
        record.save()
        messages.info(request, f'Compliance Record {record.compliance_number} moved to review.')
    return redirect('contracts:compliance_detail', pk=record.pk)


# =============================================================================
# TRADE DOCUMENTATION VIEWS
# =============================================================================

@login_required
def trade_doc_list_view(request):
    tenant = request.tenant
    documents = TradeDocument.objects.filter(tenant=tenant).select_related(
        'vendor', 'created_by',
    )
    status_choices = TradeDocument.STATUS_CHOICES
    type_choices = TradeDocument.DOCUMENT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        documents = documents.filter(
            Q(document_number__icontains=search_query)
            | Q(reference_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        documents = documents.filter(status=status_filter)

    type_filter = request.GET.get('document_type', '').strip()
    if type_filter:
        documents = documents.filter(document_type=type_filter)

    return render(request, 'contracts/trade_doc_list.html', {
        'documents': documents,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def trade_doc_create_view(request):
    tenant = request.tenant
    form = TradeDocumentForm(request.POST or None, tenant=tenant)
    formset = TradeDocumentItemFormSet(request.POST or None, prefix='line_items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        doc = form.save(commit=False)
        doc.tenant = tenant
        doc.created_by = request.user
        doc.save()
        formset.instance = doc
        formset.save()
        messages.success(request, f'Trade Document {doc.document_number} created successfully.')
        return redirect('contracts:trade_doc_detail', pk=doc.pk)

    return render(request, 'contracts/trade_doc_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Trade Document',
    })


@login_required
def trade_doc_detail_view(request, pk):
    tenant = request.tenant
    doc = get_object_or_404(TradeDocument, pk=pk, tenant=tenant)
    line_items = doc.line_items.all()

    return render(request, 'contracts/trade_doc_detail.html', {
        'doc': doc,
        'line_items': line_items,
    })


@login_required
def trade_doc_edit_view(request, pk):
    tenant = request.tenant
    doc = get_object_or_404(TradeDocument, pk=pk, tenant=tenant, status='draft')
    form = TradeDocumentForm(request.POST or None, instance=doc, tenant=tenant)
    formset = TradeDocumentItemFormSet(
        request.POST or None, instance=doc, prefix='line_items',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Trade Document {doc.document_number} updated successfully.')
        return redirect('contracts:trade_doc_detail', pk=doc.pk)

    return render(request, 'contracts/trade_doc_form.html', {
        'form': form,
        'formset': formset,
        'doc': doc,
        'title': 'Edit Trade Document',
    })


@login_required
def trade_doc_delete_view(request, pk):
    doc = get_object_or_404(
        TradeDocument, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Trade Document deleted successfully.')
        return redirect('contracts:trade_doc_list')
    return redirect('contracts:trade_doc_list')


@login_required
def trade_doc_issue_view(request, pk):
    doc = get_object_or_404(
        TradeDocument, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        doc.status = 'issued'
        doc.issue_date = doc.issue_date or timezone.now().date()
        doc.save()
        messages.success(request, f'Trade Document {doc.document_number} issued.')
    return redirect('contracts:trade_doc_detail', pk=doc.pk)


@login_required
def trade_doc_transit_view(request, pk):
    doc = get_object_or_404(
        TradeDocument, pk=pk, tenant=request.tenant, status='issued',
    )
    if request.method == 'POST':
        doc.status = 'in_transit'
        doc.save()
        messages.success(request, f'Trade Document {doc.document_number} marked as in transit.')
    return redirect('contracts:trade_doc_detail', pk=doc.pk)


@login_required
def trade_doc_deliver_view(request, pk):
    doc = get_object_or_404(
        TradeDocument, pk=pk, tenant=request.tenant, status='in_transit',
    )
    if request.method == 'POST':
        doc.status = 'delivered'
        doc.save()
        messages.success(request, f'Trade Document {doc.document_number} marked as delivered.')
    return redirect('contracts:trade_doc_detail', pk=doc.pk)


@login_required
def trade_doc_archive_view(request, pk):
    doc = get_object_or_404(TradeDocument, pk=pk, tenant=request.tenant)
    if doc.status not in ('delivered', 'issued'):
        return redirect('contracts:trade_doc_detail', pk=doc.pk)
    if request.method == 'POST':
        doc.status = 'archived'
        doc.save()
        messages.info(request, f'Trade Document {doc.document_number} archived.')
    return redirect('contracts:trade_doc_detail', pk=doc.pk)


# =============================================================================
# LICENSE MANAGEMENT VIEWS
# =============================================================================

@login_required
def license_list_view(request):
    tenant = request.tenant
    licenses = License.objects.filter(tenant=tenant).select_related('created_by')
    status_choices = License.STATUS_CHOICES
    type_choices = License.LICENSE_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        licenses = licenses.filter(
            Q(license_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(issuing_authority__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        licenses = licenses.filter(status=status_filter)

    type_filter = request.GET.get('license_type', '').strip()
    if type_filter:
        licenses = licenses.filter(license_type=type_filter)

    return render(request, 'contracts/license_list.html', {
        'licenses': licenses,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def license_create_view(request):
    form = LicenseForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        lic = form.save(commit=False)
        lic.tenant = request.tenant
        lic.created_by = request.user
        lic.save()
        messages.success(request, f'License {lic.license_number} created successfully.')
        return redirect('contracts:license_detail', pk=lic.pk)

    return render(request, 'contracts/license_form.html', {
        'form': form,
        'title': 'New License',
    })


@login_required
def license_detail_view(request, pk):
    lic = get_object_or_404(License, pk=pk, tenant=request.tenant)

    return render(request, 'contracts/license_detail.html', {
        'license': lic,
    })


@login_required
def license_edit_view(request, pk):
    lic = get_object_or_404(License, pk=pk, tenant=request.tenant, status='draft')
    form = LicenseForm(request.POST or None, instance=lic)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'License {lic.license_number} updated successfully.')
        return redirect('contracts:license_detail', pk=lic.pk)

    return render(request, 'contracts/license_form.html', {
        'form': form,
        'license': lic,
        'title': 'Edit License',
    })


@login_required
def license_delete_view(request, pk):
    lic = get_object_or_404(
        License, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        lic.delete()
        messages.success(request, 'License deleted successfully.')
        return redirect('contracts:license_list')
    return redirect('contracts:license_list')


@login_required
def license_activate_view(request, pk):
    lic = get_object_or_404(
        License, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        lic.status = 'active'
        lic.save()
        messages.success(request, f'License {lic.license_number} activated.')
    return redirect('contracts:license_detail', pk=lic.pk)


@login_required
def license_suspend_view(request, pk):
    lic = get_object_or_404(
        License, pk=pk, tenant=request.tenant, status='active',
    )
    if request.method == 'POST':
        lic.status = 'suspended'
        lic.save()
        messages.warning(request, f'License {lic.license_number} suspended.')
    return redirect('contracts:license_detail', pk=lic.pk)


@login_required
def license_revoke_view(request, pk):
    lic = get_object_or_404(License, pk=pk, tenant=request.tenant)
    if lic.status not in ('active', 'suspended', 'expiring_soon'):
        return redirect('contracts:license_detail', pk=lic.pk)
    if request.method == 'POST':
        lic.status = 'revoked'
        lic.save()
        messages.warning(request, f'License {lic.license_number} revoked.')
    return redirect('contracts:license_detail', pk=lic.pk)


@login_required
def license_expire_view(request, pk):
    lic = get_object_or_404(License, pk=pk, tenant=request.tenant)
    if lic.status not in ('active', 'expiring_soon'):
        return redirect('contracts:license_detail', pk=lic.pk)
    if request.method == 'POST':
        lic.status = 'expired'
        lic.save()
        messages.info(request, f'License {lic.license_number} marked as expired.')
    return redirect('contracts:license_detail', pk=lic.pk)


# =============================================================================
# SUSTAINABILITY TRACKING VIEWS
# =============================================================================

@login_required
def sustainability_list_view(request):
    tenant = request.tenant
    reports = SustainabilityReport.objects.filter(tenant=tenant).select_related(
        'created_by',
    )
    status_choices = SustainabilityReport.STATUS_CHOICES
    type_choices = SustainabilityReport.REPORT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reports = reports.filter(
            Q(report_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reports = reports.filter(status=status_filter)

    type_filter = request.GET.get('report_type', '').strip()
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    return render(request, 'contracts/sustainability_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def sustainability_create_view(request):
    form = SustainabilityReportForm(request.POST or None)
    formset = SustainabilityMetricFormSet(request.POST or None, prefix='metrics')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        report = form.save(commit=False)
        report.tenant = request.tenant
        report.created_by = request.user
        report.save()
        formset.instance = report
        formset.save()
        messages.success(request, f'Sustainability Report {report.report_number} created successfully.')
        return redirect('contracts:sustainability_detail', pk=report.pk)

    return render(request, 'contracts/sustainability_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Sustainability Report',
    })


@login_required
def sustainability_detail_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant,
    )
    metrics = report.metrics.all()

    return render(request, 'contracts/sustainability_detail.html', {
        'report': report,
        'metrics': metrics,
    })


@login_required
def sustainability_edit_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant, status='draft',
    )
    form = SustainabilityReportForm(request.POST or None, instance=report)
    formset = SustainabilityMetricFormSet(
        request.POST or None, instance=report, prefix='metrics',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Sustainability Report {report.report_number} updated successfully.')
        return redirect('contracts:sustainability_detail', pk=report.pk)

    return render(request, 'contracts/sustainability_form.html', {
        'form': form,
        'formset': formset,
        'report': report,
        'title': 'Edit Sustainability Report',
    })


@login_required
def sustainability_delete_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Sustainability Report deleted successfully.')
        return redirect('contracts:sustainability_list')
    return redirect('contracts:sustainability_list')


@login_required
def sustainability_submit_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        report.status = 'submitted'
        report.save()
        messages.success(request, f'Report {report.report_number} submitted.')
    return redirect('contracts:sustainability_detail', pk=report.pk)


@login_required
def sustainability_review_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant, status='submitted',
    )
    if request.method == 'POST':
        report.status = 'reviewed'
        report.save()
        messages.success(request, f'Report {report.report_number} reviewed.')
    return redirect('contracts:sustainability_detail', pk=report.pk)


@login_required
def sustainability_approve_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant, status='reviewed',
    )
    if request.method == 'POST':
        report.status = 'approved'
        report.save()
        messages.success(request, f'Report {report.report_number} approved.')
    return redirect('contracts:sustainability_detail', pk=report.pk)


@login_required
def sustainability_publish_view(request, pk):
    report = get_object_or_404(
        SustainabilityReport, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        report.status = 'published'
        report.save()
        messages.success(request, f'Report {report.report_number} published.')
    return redirect('contracts:sustainability_detail', pk=report.pk)
