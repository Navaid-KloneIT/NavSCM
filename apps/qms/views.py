from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AuditFindingFormSet,
    CAPAActionFormSet,
    CAPAForm,
    CertificateOfAnalysisForm,
    CoATestResultFormSet,
    InspectionCriteriaFormSet,
    InspectionResultFormSet,
    InspectionTemplateForm,
    NonConformanceReportForm,
    QualityAuditForm,
    QualityInspectionForm,
)
from .models import (
    CAPA,
    CertificateOfAnalysis,
    InspectionTemplate,
    NonConformanceReport,
    QualityAudit,
    QualityInspection,
)


# =============================================================================
# INSPECTION TEMPLATE VIEWS
# =============================================================================

@login_required
def template_list_view(request):
    tenant = request.tenant
    templates = InspectionTemplate.objects.filter(tenant=tenant)
    type_choices = InspectionTemplate.INSPECTION_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        templates = templates.filter(inspection_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        templates = templates.filter(is_active=True)
    elif status_filter == 'inactive':
        templates = templates.filter(is_active=False)

    return render(request, 'qms/template_list.html', {
        'templates': templates,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def template_create_view(request):
    tenant = request.tenant
    form = InspectionTemplateForm(request.POST or None, tenant=tenant)
    formset = InspectionCriteriaFormSet(request.POST or None, prefix='criteria')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        template = form.save(commit=False)
        template.tenant = tenant
        template.created_by = request.user
        template.save()
        formset.instance = template
        formset.save()
        messages.success(request, f'Inspection Template "{template.name}" created successfully.')
        return redirect('qms:template_detail', pk=template.pk)

    return render(request, 'qms/template_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Inspection Template',
    })


@login_required
def template_detail_view(request, pk):
    tenant = request.tenant
    template = get_object_or_404(InspectionTemplate, pk=pk, tenant=tenant)
    criteria = template.criteria.all()

    return render(request, 'qms/template_detail.html', {
        'template': template,
        'criteria': criteria,
    })


@login_required
def template_edit_view(request, pk):
    tenant = request.tenant
    template = get_object_or_404(InspectionTemplate, pk=pk, tenant=tenant)
    form = InspectionTemplateForm(request.POST or None, instance=template, tenant=tenant)
    formset = InspectionCriteriaFormSet(
        request.POST or None, instance=template, prefix='criteria',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Inspection Template "{template.name}" updated successfully.')
        return redirect('qms:template_detail', pk=template.pk)

    return render(request, 'qms/template_form.html', {
        'form': form,
        'formset': formset,
        'template': template,
        'title': 'Edit Inspection Template',
    })


@login_required
def template_delete_view(request, pk):
    template = get_object_or_404(InspectionTemplate, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Inspection Template deleted successfully.')
        return redirect('qms:template_list')
    return redirect('qms:template_list')


# =============================================================================
# QUALITY INSPECTION VIEWS
# =============================================================================

@login_required
def inspection_list_view(request):
    tenant = request.tenant
    inspections = QualityInspection.objects.filter(tenant=tenant).select_related(
        'item', 'inspector', 'template',
    )
    status_choices = QualityInspection.STATUS_CHOICES
    type_choices = QualityInspection.INSPECTION_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        inspections = inspections.filter(
            Q(inspection_number__icontains=search_query)
            | Q(item__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        inspections = inspections.filter(status=status_filter)

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        inspections = inspections.filter(inspection_type=type_filter)

    return render(request, 'qms/inspection_list.html', {
        'inspections': inspections,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def inspection_create_view(request):
    tenant = request.tenant
    form = QualityInspectionForm(request.POST or None, tenant=tenant)
    formset = InspectionResultFormSet(request.POST or None, prefix='results')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        inspection = form.save(commit=False)
        inspection.tenant = tenant
        inspection.created_by = request.user
        inspection.save()
        formset.instance = inspection
        formset.save()
        messages.success(request, f'Inspection {inspection.inspection_number} created successfully.')
        return redirect('qms:inspection_detail', pk=inspection.pk)

    return render(request, 'qms/inspection_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Quality Inspection',
    })


@login_required
def inspection_detail_view(request, pk):
    tenant = request.tenant
    inspection = get_object_or_404(QualityInspection, pk=pk, tenant=tenant)
    results = inspection.results.select_related('criteria')

    return render(request, 'qms/inspection_detail.html', {
        'inspection': inspection,
        'results': results,
    })


@login_required
def inspection_edit_view(request, pk):
    tenant = request.tenant
    inspection = get_object_or_404(QualityInspection, pk=pk, tenant=tenant, status='draft')
    form = QualityInspectionForm(request.POST or None, instance=inspection, tenant=tenant)
    formset = InspectionResultFormSet(
        request.POST or None, instance=inspection, prefix='results',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Inspection {inspection.inspection_number} updated successfully.')
        return redirect('qms:inspection_detail', pk=inspection.pk)

    return render(request, 'qms/inspection_form.html', {
        'form': form,
        'formset': formset,
        'inspection': inspection,
        'title': 'Edit Quality Inspection',
    })


@login_required
def inspection_start_view(request, pk):
    inspection = get_object_or_404(
        QualityInspection, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        inspection.status = 'in_progress'
        inspection.save()
        messages.success(request, f'Inspection {inspection.inspection_number} started.')
    return redirect('qms:inspection_detail', pk=inspection.pk)


@login_required
def inspection_complete_view(request, pk):
    inspection = get_object_or_404(
        QualityInspection, pk=pk, tenant=request.tenant, status='in_progress',
    )
    if request.method == 'POST':
        if inspection.results.filter(result='fail').exists():
            inspection.status = 'failed'
        else:
            inspection.status = 'completed'
        inspection.save()
        messages.success(request, f'Inspection {inspection.inspection_number} {inspection.get_status_display().lower()}.')
    return redirect('qms:inspection_detail', pk=inspection.pk)


@login_required
def inspection_hold_view(request, pk):
    inspection = get_object_or_404(
        QualityInspection, pk=pk, tenant=request.tenant, status='in_progress',
    )
    if request.method == 'POST':
        inspection.status = 'on_hold'
        inspection.save()
        messages.success(request, f'Inspection {inspection.inspection_number} put on hold.')
    return redirect('qms:inspection_detail', pk=inspection.pk)


@login_required
def inspection_delete_view(request, pk):
    inspection = get_object_or_404(
        QualityInspection, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        inspection.delete()
        messages.success(request, 'Inspection deleted successfully.')
        return redirect('qms:inspection_list')
    return redirect('qms:inspection_list')


# =============================================================================
# NON-CONFORMANCE REPORT VIEWS
# =============================================================================

@login_required
def ncr_list_view(request):
    tenant = request.tenant
    ncrs = NonConformanceReport.objects.filter(tenant=tenant).select_related(
        'item', 'reported_by', 'assigned_to',
    )
    status_choices = NonConformanceReport.STATUS_CHOICES
    severity_choices = NonConformanceReport.SEVERITY_CHOICES
    source_choices = NonConformanceReport.SOURCE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        ncrs = ncrs.filter(
            Q(ncr_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        ncrs = ncrs.filter(status=status_filter)

    severity_filter = request.GET.get('severity', '').strip()
    if severity_filter:
        ncrs = ncrs.filter(severity=severity_filter)

    source_filter = request.GET.get('source', '').strip()
    if source_filter:
        ncrs = ncrs.filter(source=source_filter)

    return render(request, 'qms/ncr_list.html', {
        'ncrs': ncrs,
        'status_choices': status_choices,
        'severity_choices': severity_choices,
        'source_choices': source_choices,
        'search_query': search_query,
    })


@login_required
def ncr_create_view(request):
    tenant = request.tenant
    form = NonConformanceReportForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        ncr = form.save(commit=False)
        ncr.tenant = tenant
        ncr.created_by = request.user
        ncr.save()
        messages.success(request, f'NCR {ncr.ncr_number} created successfully.')
        return redirect('qms:ncr_detail', pk=ncr.pk)

    return render(request, 'qms/ncr_form.html', {
        'form': form,
        'title': 'New Non-Conformance Report',
    })


@login_required
def ncr_detail_view(request, pk):
    tenant = request.tenant
    ncr = get_object_or_404(NonConformanceReport, pk=pk, tenant=tenant)
    capas = ncr.capas.all()

    return render(request, 'qms/ncr_detail.html', {
        'ncr': ncr,
        'capas': capas,
    })


@login_required
def ncr_edit_view(request, pk):
    tenant = request.tenant
    ncr = get_object_or_404(NonConformanceReport, pk=pk, tenant=tenant, status='draft')
    form = NonConformanceReportForm(request.POST or None, instance=ncr, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'NCR {ncr.ncr_number} updated successfully.')
        return redirect('qms:ncr_detail', pk=ncr.pk)

    return render(request, 'qms/ncr_form.html', {
        'form': form,
        'ncr': ncr,
        'title': 'Edit Non-Conformance Report',
    })


@login_required
def ncr_open_view(request, pk):
    ncr = get_object_or_404(
        NonConformanceReport, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        ncr.status = 'open'
        ncr.save()
        messages.success(request, f'NCR {ncr.ncr_number} opened.')
    return redirect('qms:ncr_detail', pk=ncr.pk)


@login_required
def ncr_investigate_view(request, pk):
    ncr = get_object_or_404(
        NonConformanceReport, pk=pk, tenant=request.tenant, status='open',
    )
    if request.method == 'POST':
        ncr.status = 'under_investigation'
        ncr.save()
        messages.success(request, f'NCR {ncr.ncr_number} moved to investigation.')
    return redirect('qms:ncr_detail', pk=ncr.pk)


@login_required
def ncr_resolve_view(request, pk):
    ncr = get_object_or_404(
        NonConformanceReport, pk=pk, tenant=request.tenant, status='under_investigation',
    )
    if request.method == 'POST':
        ncr.status = 'resolved'
        ncr.save()
        messages.success(request, f'NCR {ncr.ncr_number} resolved.')
    return redirect('qms:ncr_detail', pk=ncr.pk)


@login_required
def ncr_close_view(request, pk):
    ncr = get_object_or_404(
        NonConformanceReport, pk=pk, tenant=request.tenant, status='resolved',
    )
    if request.method == 'POST':
        ncr.status = 'closed'
        ncr.closed_date = timezone.now().date()
        ncr.save()
        messages.success(request, f'NCR {ncr.ncr_number} closed.')
    return redirect('qms:ncr_detail', pk=ncr.pk)


@login_required
def ncr_delete_view(request, pk):
    ncr = get_object_or_404(
        NonConformanceReport, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        ncr.delete()
        messages.success(request, 'NCR deleted successfully.')
        return redirect('qms:ncr_list')
    return redirect('qms:ncr_list')


# =============================================================================
# CAPA VIEWS
# =============================================================================

@login_required
def capa_list_view(request):
    tenant = request.tenant
    capas = CAPA.objects.filter(tenant=tenant).select_related(
        'ncr', 'assigned_to', 'created_by',
    )
    status_choices = CAPA.STATUS_CHOICES
    type_choices = CAPA.CAPA_TYPE_CHOICES
    priority_choices = CAPA.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        capas = capas.filter(
            Q(capa_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        capas = capas.filter(status=status_filter)

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        capas = capas.filter(capa_type=type_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        capas = capas.filter(priority=priority_filter)

    return render(request, 'qms/capa_list.html', {
        'capas': capas,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def capa_create_view(request):
    tenant = request.tenant
    form = CAPAForm(request.POST or None, tenant=tenant)
    formset = CAPAActionFormSet(
        request.POST or None, prefix='actions',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        capa = form.save(commit=False)
        capa.tenant = tenant
        capa.created_by = request.user
        capa.save()
        formset.instance = capa
        formset.save()
        messages.success(request, f'CAPA {capa.capa_number} created successfully.')
        return redirect('qms:capa_detail', pk=capa.pk)

    return render(request, 'qms/capa_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New CAPA',
    })


@login_required
def capa_detail_view(request, pk):
    tenant = request.tenant
    capa = get_object_or_404(CAPA, pk=pk, tenant=tenant)
    actions = capa.actions.select_related('assigned_to')

    return render(request, 'qms/capa_detail.html', {
        'capa': capa,
        'actions': actions,
    })


@login_required
def capa_edit_view(request, pk):
    tenant = request.tenant
    capa = get_object_or_404(CAPA, pk=pk, tenant=tenant, status='draft')
    form = CAPAForm(request.POST or None, instance=capa, tenant=tenant)
    formset = CAPAActionFormSet(
        request.POST or None, instance=capa, prefix='actions',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'CAPA {capa.capa_number} updated successfully.')
        return redirect('qms:capa_detail', pk=capa.pk)

    return render(request, 'qms/capa_form.html', {
        'form': form,
        'formset': formset,
        'capa': capa,
        'title': 'Edit CAPA',
    })


@login_required
def capa_open_view(request, pk):
    capa = get_object_or_404(CAPA, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        capa.status = 'open'
        capa.save()
        messages.success(request, f'CAPA {capa.capa_number} opened.')
    return redirect('qms:capa_detail', pk=capa.pk)


@login_required
def capa_start_view(request, pk):
    capa = get_object_or_404(CAPA, pk=pk, tenant=request.tenant, status='open')
    if request.method == 'POST':
        capa.status = 'in_progress'
        capa.save()
        messages.success(request, f'CAPA {capa.capa_number} started.')
    return redirect('qms:capa_detail', pk=capa.pk)


@login_required
def capa_verify_view(request, pk):
    capa = get_object_or_404(CAPA, pk=pk, tenant=request.tenant, status='in_progress')
    if request.method == 'POST':
        capa.status = 'verification'
        capa.save()
        messages.success(request, f'CAPA {capa.capa_number} moved to verification.')
    return redirect('qms:capa_detail', pk=capa.pk)


@login_required
def capa_complete_view(request, pk):
    capa = get_object_or_404(CAPA, pk=pk, tenant=request.tenant, status='verification')
    if request.method == 'POST':
        capa.status = 'completed'
        capa.completed_date = timezone.now().date()
        capa.save()
        messages.success(request, f'CAPA {capa.capa_number} completed.')
    return redirect('qms:capa_detail', pk=capa.pk)


@login_required
def capa_close_view(request, pk):
    capa = get_object_or_404(CAPA, pk=pk, tenant=request.tenant, status='completed')
    if request.method == 'POST':
        capa.status = 'closed'
        capa.save()
        messages.success(request, f'CAPA {capa.capa_number} closed.')
    return redirect('qms:capa_detail', pk=capa.pk)


@login_required
def capa_delete_view(request, pk):
    capa = get_object_or_404(CAPA, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        capa.delete()
        messages.success(request, 'CAPA deleted successfully.')
        return redirect('qms:capa_list')
    return redirect('qms:capa_list')


# =============================================================================
# QUALITY AUDIT VIEWS
# =============================================================================

@login_required
def audit_list_view(request):
    tenant = request.tenant
    audits = QualityAudit.objects.filter(tenant=tenant).select_related(
        'lead_auditor', 'created_by',
    )
    status_choices = QualityAudit.STATUS_CHOICES
    type_choices = QualityAudit.AUDIT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        audits = audits.filter(
            Q(audit_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        audits = audits.filter(status=status_filter)

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        audits = audits.filter(audit_type=type_filter)

    return render(request, 'qms/audit_list.html', {
        'audits': audits,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def audit_create_view(request):
    tenant = request.tenant
    form = QualityAuditForm(request.POST or None, tenant=tenant)
    formset = AuditFindingFormSet(
        request.POST or None, prefix='findings',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        audit = form.save(commit=False)
        audit.tenant = tenant
        audit.created_by = request.user
        audit.save()
        formset.instance = audit
        formset.save()
        messages.success(request, f'Audit {audit.audit_number} created successfully.')
        return redirect('qms:audit_detail', pk=audit.pk)

    return render(request, 'qms/audit_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Quality Audit',
    })


@login_required
def audit_detail_view(request, pk):
    tenant = request.tenant
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=tenant)
    findings = audit.findings.select_related('assigned_to')

    return render(request, 'qms/audit_detail.html', {
        'audit': audit,
        'findings': findings,
    })


@login_required
def audit_edit_view(request, pk):
    tenant = request.tenant
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=tenant, status='draft')
    form = QualityAuditForm(request.POST or None, instance=audit, tenant=tenant)
    formset = AuditFindingFormSet(
        request.POST or None, instance=audit, prefix='findings',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Audit {audit.audit_number} updated successfully.')
        return redirect('qms:audit_detail', pk=audit.pk)

    return render(request, 'qms/audit_form.html', {
        'form': form,
        'formset': formset,
        'audit': audit,
        'title': 'Edit Quality Audit',
    })


@login_required
def audit_schedule_view(request, pk):
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        audit.status = 'scheduled'
        audit.save()
        messages.success(request, f'Audit {audit.audit_number} scheduled.')
    return redirect('qms:audit_detail', pk=audit.pk)


@login_required
def audit_start_view(request, pk):
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=request.tenant, status='scheduled')
    if request.method == 'POST':
        audit.status = 'in_progress'
        audit.save()
        messages.success(request, f'Audit {audit.audit_number} started.')
    return redirect('qms:audit_detail', pk=audit.pk)


@login_required
def audit_complete_view(request, pk):
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=request.tenant, status='in_progress')
    if request.method == 'POST':
        audit.status = 'completed'
        audit.completion_date = timezone.now().date()
        audit.save()
        messages.success(request, f'Audit {audit.audit_number} completed.')
    return redirect('qms:audit_detail', pk=audit.pk)


@login_required
def audit_close_view(request, pk):
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=request.tenant, status='completed')
    if request.method == 'POST':
        audit.status = 'closed'
        audit.save()
        messages.success(request, f'Audit {audit.audit_number} closed.')
    return redirect('qms:audit_detail', pk=audit.pk)


@login_required
def audit_delete_view(request, pk):
    audit = get_object_or_404(QualityAudit, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        audit.delete()
        messages.success(request, 'Audit deleted successfully.')
        return redirect('qms:audit_list')
    return redirect('qms:audit_list')


# =============================================================================
# CERTIFICATE OF ANALYSIS VIEWS
# =============================================================================

@login_required
def coa_list_view(request):
    tenant = request.tenant
    coas = CertificateOfAnalysis.objects.filter(tenant=tenant).select_related(
        'item', 'created_by', 'approved_by',
    )
    status_choices = CertificateOfAnalysis.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        coas = coas.filter(
            Q(coa_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(batch_number__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        coas = coas.filter(status=status_filter)

    return render(request, 'qms/coa_list.html', {
        'coas': coas,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def coa_create_view(request):
    tenant = request.tenant
    form = CertificateOfAnalysisForm(request.POST or None, tenant=tenant)
    formset = CoATestResultFormSet(request.POST or None, prefix='tests')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        coa = form.save(commit=False)
        coa.tenant = tenant
        coa.created_by = request.user
        coa.save()
        formset.instance = coa
        formset.save()
        messages.success(request, f'CoA {coa.coa_number} created successfully.')
        return redirect('qms:coa_detail', pk=coa.pk)

    return render(request, 'qms/coa_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Certificate of Analysis',
    })


@login_required
def coa_detail_view(request, pk):
    tenant = request.tenant
    coa = get_object_or_404(CertificateOfAnalysis, pk=pk, tenant=tenant)
    test_results = coa.test_results.all()

    return render(request, 'qms/coa_detail.html', {
        'coa': coa,
        'test_results': test_results,
    })


@login_required
def coa_edit_view(request, pk):
    tenant = request.tenant
    coa = get_object_or_404(CertificateOfAnalysis, pk=pk, tenant=tenant, status='draft')
    form = CertificateOfAnalysisForm(request.POST or None, instance=coa, tenant=tenant)
    formset = CoATestResultFormSet(
        request.POST or None, instance=coa, prefix='tests',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'CoA {coa.coa_number} updated successfully.')
        return redirect('qms:coa_detail', pk=coa.pk)

    return render(request, 'qms/coa_form.html', {
        'form': form,
        'formset': formset,
        'coa': coa,
        'title': 'Edit Certificate of Analysis',
    })


@login_required
def coa_submit_view(request, pk):
    coa = get_object_or_404(
        CertificateOfAnalysis, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        coa.status = 'pending_review'
        coa.save()
        messages.success(request, f'CoA {coa.coa_number} submitted for review.')
    return redirect('qms:coa_detail', pk=coa.pk)


@login_required
def coa_approve_view(request, pk):
    coa = get_object_or_404(
        CertificateOfAnalysis, pk=pk, tenant=request.tenant, status='pending_review',
    )
    if request.method == 'POST':
        coa.status = 'approved'
        coa.approved_by = request.user
        coa.approved_date = timezone.now().date()
        coa.save()
        messages.success(request, f'CoA {coa.coa_number} approved.')
    return redirect('qms:coa_detail', pk=coa.pk)


@login_required
def coa_issue_view(request, pk):
    coa = get_object_or_404(
        CertificateOfAnalysis, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        coa.status = 'issued'
        coa.save()
        messages.success(request, f'CoA {coa.coa_number} issued.')
    return redirect('qms:coa_detail', pk=coa.pk)


@login_required
def coa_revoke_view(request, pk):
    coa = get_object_or_404(
        CertificateOfAnalysis, pk=pk, tenant=request.tenant, status='issued',
    )
    if request.method == 'POST':
        coa.status = 'revoked'
        coa.save()
        messages.warning(request, f'CoA {coa.coa_number} revoked.')
    return redirect('qms:coa_detail', pk=coa.pk)


@login_required
def coa_delete_view(request, pk):
    coa = get_object_or_404(
        CertificateOfAnalysis, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        coa.delete()
        messages.success(request, 'Certificate of Analysis deleted successfully.')
        return redirect('qms:coa_list')
    return redirect('qms:coa_list')
