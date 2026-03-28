from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    FinancialReportForm,
    FinancialReportItemFormSet,
    InventoryAnalyticsForm,
    InventoryAnalyticsItemFormSet,
    LogisticsKPIForm,
    LogisticsKPIItemFormSet,
    PredictiveAlertForm,
    ProcurementAnalyticsForm,
    ProcurementAnalyticsItemFormSet,
)
from .models import (
    FinancialReport,
    InventoryAnalytics,
    LogisticsKPI,
    PredictiveAlert,
    ProcurementAnalytics,
)


# =============================================================================
# ANALYTICS DASHBOARD
# =============================================================================

@login_required
def dashboard_view(request):
    tenant = request.tenant
    context = {
        'inventory_count': InventoryAnalytics.objects.filter(tenant=tenant).count(),
        'procurement_count': ProcurementAnalytics.objects.filter(tenant=tenant).count(),
        'logistics_count': LogisticsKPI.objects.filter(tenant=tenant).count(),
        'financial_count': FinancialReport.objects.filter(tenant=tenant).count(),
        'alert_count': PredictiveAlert.objects.filter(tenant=tenant).exclude(status__in=['resolved', 'dismissed']).count(),
        'recent_inventory': InventoryAnalytics.objects.filter(tenant=tenant)[:5],
        'recent_procurement': ProcurementAnalytics.objects.filter(tenant=tenant)[:5],
        'recent_logistics': LogisticsKPI.objects.filter(tenant=tenant)[:5],
        'recent_financial': FinancialReport.objects.filter(tenant=tenant)[:5],
        'recent_alerts': PredictiveAlert.objects.filter(tenant=tenant).exclude(status__in=['resolved', 'dismissed'])[:5],
    }
    return render(request, 'analytics/dashboard.html', context)


# =============================================================================
# INVENTORY ANALYTICS VIEWS
# =============================================================================

@login_required
def inventory_list_view(request):
    tenant = request.tenant
    reports = InventoryAnalytics.objects.filter(tenant=tenant)
    status_choices = InventoryAnalytics.STATUS_CHOICES
    type_choices = InventoryAnalytics.REPORT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reports = reports.filter(Q(report_number__icontains=search_query))

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reports = reports.filter(status=status_filter)

    type_filter = request.GET.get('report_type', '').strip()
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    return render(request, 'analytics/inventory_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def inventory_create_view(request):
    tenant = request.tenant
    form = InventoryAnalyticsForm(request.POST or None, tenant=tenant)
    formset = InventoryAnalyticsItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        report = form.save(commit=False)
        report.tenant = tenant
        report.created_by = request.user
        report.save()
        formset.instance = report
        formset.save()
        messages.success(request, f'Inventory Report {report.report_number} created successfully.')
        return redirect('analytics:inventory_detail', pk=report.pk)

    return render(request, 'analytics/inventory_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Inventory Analytics Report',
    })


@login_required
def inventory_detail_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(InventoryAnalytics, pk=pk, tenant=tenant)
    items = report.items.select_related('item', 'warehouse')
    return render(request, 'analytics/inventory_detail.html', {
        'report': report,
        'items': items,
    })


@login_required
def inventory_edit_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(InventoryAnalytics, pk=pk, tenant=tenant, status='draft')
    form = InventoryAnalyticsForm(request.POST or None, instance=report, tenant=tenant)
    formset = InventoryAnalyticsItemFormSet(
        request.POST or None, instance=report, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Inventory Report {report.report_number} updated successfully.')
        return redirect('analytics:inventory_detail', pk=report.pk)

    return render(request, 'analytics/inventory_form.html', {
        'form': form,
        'formset': formset,
        'report': report,
        'title': 'Edit Inventory Analytics Report',
    })


@login_required
def inventory_delete_view(request, pk):
    report = get_object_or_404(InventoryAnalytics, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Inventory Report deleted successfully.')
        return redirect('analytics:inventory_list')
    return redirect('analytics:inventory_list')


@login_required
def inventory_generate_view(request, pk):
    report = get_object_or_404(InventoryAnalytics, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.status = 'generated'
        report.save()
        messages.success(request, f'Report {report.report_number} generated.')
    return redirect('analytics:inventory_detail', pk=report.pk)


@login_required
def inventory_review_view(request, pk):
    report = get_object_or_404(InventoryAnalytics, pk=pk, tenant=request.tenant, status='generated')
    if request.method == 'POST':
        report.status = 'reviewed'
        report.save()
        messages.success(request, f'Report {report.report_number} reviewed.')
    return redirect('analytics:inventory_detail', pk=report.pk)


@login_required
def inventory_archive_view(request, pk):
    report = get_object_or_404(InventoryAnalytics, pk=pk, tenant=request.tenant, status='reviewed')
    if request.method == 'POST':
        report.status = 'archived'
        report.save()
        messages.success(request, f'Report {report.report_number} archived.')
    return redirect('analytics:inventory_detail', pk=report.pk)


# =============================================================================
# PROCUREMENT ANALYTICS VIEWS
# =============================================================================

@login_required
def procurement_list_view(request):
    tenant = request.tenant
    reports = ProcurementAnalytics.objects.filter(tenant=tenant)
    status_choices = ProcurementAnalytics.STATUS_CHOICES
    type_choices = ProcurementAnalytics.REPORT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reports = reports.filter(Q(report_number__icontains=search_query))

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reports = reports.filter(status=status_filter)

    type_filter = request.GET.get('report_type', '').strip()
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    return render(request, 'analytics/procurement_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def procurement_create_view(request):
    tenant = request.tenant
    form = ProcurementAnalyticsForm(request.POST or None, tenant=tenant)
    formset = ProcurementAnalyticsItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        report = form.save(commit=False)
        report.tenant = tenant
        report.created_by = request.user
        report.save()
        formset.instance = report
        formset.save()
        messages.success(request, f'Procurement Report {report.report_number} created successfully.')
        return redirect('analytics:procurement_detail', pk=report.pk)

    return render(request, 'analytics/procurement_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Procurement Analytics Report',
    })


@login_required
def procurement_detail_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(ProcurementAnalytics, pk=pk, tenant=tenant)
    items = report.items.select_related('vendor')
    return render(request, 'analytics/procurement_detail.html', {
        'report': report,
        'items': items,
    })


@login_required
def procurement_edit_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(ProcurementAnalytics, pk=pk, tenant=tenant, status='draft')
    form = ProcurementAnalyticsForm(request.POST or None, instance=report, tenant=tenant)
    formset = ProcurementAnalyticsItemFormSet(
        request.POST or None, instance=report, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Procurement Report {report.report_number} updated successfully.')
        return redirect('analytics:procurement_detail', pk=report.pk)

    return render(request, 'analytics/procurement_form.html', {
        'form': form,
        'formset': formset,
        'report': report,
        'title': 'Edit Procurement Analytics Report',
    })


@login_required
def procurement_delete_view(request, pk):
    report = get_object_or_404(ProcurementAnalytics, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Procurement Report deleted successfully.')
        return redirect('analytics:procurement_list')
    return redirect('analytics:procurement_list')


@login_required
def procurement_generate_view(request, pk):
    report = get_object_or_404(ProcurementAnalytics, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.status = 'generated'
        report.save()
        messages.success(request, f'Report {report.report_number} generated.')
    return redirect('analytics:procurement_detail', pk=report.pk)


@login_required
def procurement_review_view(request, pk):
    report = get_object_or_404(ProcurementAnalytics, pk=pk, tenant=request.tenant, status='generated')
    if request.method == 'POST':
        report.status = 'reviewed'
        report.save()
        messages.success(request, f'Report {report.report_number} reviewed.')
    return redirect('analytics:procurement_detail', pk=report.pk)


@login_required
def procurement_archive_view(request, pk):
    report = get_object_or_404(ProcurementAnalytics, pk=pk, tenant=request.tenant, status='reviewed')
    if request.method == 'POST':
        report.status = 'archived'
        report.save()
        messages.success(request, f'Report {report.report_number} archived.')
    return redirect('analytics:procurement_detail', pk=report.pk)


# =============================================================================
# LOGISTICS KPI VIEWS
# =============================================================================

@login_required
def logistics_list_view(request):
    tenant = request.tenant
    reports = LogisticsKPI.objects.filter(tenant=tenant)
    status_choices = LogisticsKPI.STATUS_CHOICES
    type_choices = LogisticsKPI.REPORT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reports = reports.filter(Q(report_number__icontains=search_query))

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reports = reports.filter(status=status_filter)

    type_filter = request.GET.get('report_type', '').strip()
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    return render(request, 'analytics/logistics_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def logistics_create_view(request):
    tenant = request.tenant
    form = LogisticsKPIForm(request.POST or None, tenant=tenant)
    formset = LogisticsKPIItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        report = form.save(commit=False)
        report.tenant = tenant
        report.created_by = request.user
        report.save()
        formset.instance = report
        formset.save()
        messages.success(request, f'Logistics KPI Report {report.report_number} created successfully.')
        return redirect('analytics:logistics_detail', pk=report.pk)

    return render(request, 'analytics/logistics_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Logistics KPI Report',
    })


@login_required
def logistics_detail_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(LogisticsKPI, pk=pk, tenant=tenant)
    items = report.items.select_related('carrier')
    return render(request, 'analytics/logistics_detail.html', {
        'report': report,
        'items': items,
    })


@login_required
def logistics_edit_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(LogisticsKPI, pk=pk, tenant=tenant, status='draft')
    form = LogisticsKPIForm(request.POST or None, instance=report, tenant=tenant)
    formset = LogisticsKPIItemFormSet(
        request.POST or None, instance=report, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Logistics KPI Report {report.report_number} updated successfully.')
        return redirect('analytics:logistics_detail', pk=report.pk)

    return render(request, 'analytics/logistics_form.html', {
        'form': form,
        'formset': formset,
        'report': report,
        'title': 'Edit Logistics KPI Report',
    })


@login_required
def logistics_delete_view(request, pk):
    report = get_object_or_404(LogisticsKPI, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Logistics KPI Report deleted successfully.')
        return redirect('analytics:logistics_list')
    return redirect('analytics:logistics_list')


@login_required
def logistics_generate_view(request, pk):
    report = get_object_or_404(LogisticsKPI, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.status = 'generated'
        report.save()
        messages.success(request, f'Report {report.report_number} generated.')
    return redirect('analytics:logistics_detail', pk=report.pk)


@login_required
def logistics_review_view(request, pk):
    report = get_object_or_404(LogisticsKPI, pk=pk, tenant=request.tenant, status='generated')
    if request.method == 'POST':
        report.status = 'reviewed'
        report.save()
        messages.success(request, f'Report {report.report_number} reviewed.')
    return redirect('analytics:logistics_detail', pk=report.pk)


@login_required
def logistics_archive_view(request, pk):
    report = get_object_or_404(LogisticsKPI, pk=pk, tenant=request.tenant, status='reviewed')
    if request.method == 'POST':
        report.status = 'archived'
        report.save()
        messages.success(request, f'Report {report.report_number} archived.')
    return redirect('analytics:logistics_detail', pk=report.pk)


# =============================================================================
# FINANCIAL REPORT VIEWS
# =============================================================================

@login_required
def financial_list_view(request):
    tenant = request.tenant
    reports = FinancialReport.objects.filter(tenant=tenant)
    status_choices = FinancialReport.STATUS_CHOICES
    type_choices = FinancialReport.REPORT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reports = reports.filter(Q(report_number__icontains=search_query))

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reports = reports.filter(status=status_filter)

    type_filter = request.GET.get('report_type', '').strip()
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    return render(request, 'analytics/financial_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def financial_create_view(request):
    tenant = request.tenant
    form = FinancialReportForm(request.POST or None, tenant=tenant)
    formset = FinancialReportItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        report = form.save(commit=False)
        report.tenant = tenant
        report.created_by = request.user
        report.save()
        formset.instance = report
        formset.save()
        messages.success(request, f'Financial Report {report.report_number} created successfully.')
        return redirect('analytics:financial_detail', pk=report.pk)

    return render(request, 'analytics/financial_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Financial Report',
    })


@login_required
def financial_detail_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(FinancialReport, pk=pk, tenant=tenant)
    items = report.items.all()
    return render(request, 'analytics/financial_detail.html', {
        'report': report,
        'items': items,
    })


@login_required
def financial_edit_view(request, pk):
    tenant = request.tenant
    report = get_object_or_404(FinancialReport, pk=pk, tenant=tenant, status='draft')
    form = FinancialReportForm(request.POST or None, instance=report, tenant=tenant)
    formset = FinancialReportItemFormSet(
        request.POST or None, instance=report, prefix='items',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Financial Report {report.report_number} updated successfully.')
        return redirect('analytics:financial_detail', pk=report.pk)

    return render(request, 'analytics/financial_form.html', {
        'form': form,
        'formset': formset,
        'report': report,
        'title': 'Edit Financial Report',
    })


@login_required
def financial_delete_view(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Financial Report deleted successfully.')
        return redirect('analytics:financial_list')
    return redirect('analytics:financial_list')


@login_required
def financial_generate_view(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        report.status = 'generated'
        report.save()
        messages.success(request, f'Report {report.report_number} generated.')
    return redirect('analytics:financial_detail', pk=report.pk)


@login_required
def financial_review_view(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk, tenant=request.tenant, status='generated')
    if request.method == 'POST':
        report.status = 'reviewed'
        report.save()
        messages.success(request, f'Report {report.report_number} reviewed.')
    return redirect('analytics:financial_detail', pk=report.pk)


@login_required
def financial_archive_view(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk, tenant=request.tenant, status='reviewed')
    if request.method == 'POST':
        report.status = 'archived'
        report.save()
        messages.success(request, f'Report {report.report_number} archived.')
    return redirect('analytics:financial_detail', pk=report.pk)


# =============================================================================
# PREDICTIVE ALERT VIEWS
# =============================================================================

@login_required
def alert_list_view(request):
    tenant = request.tenant
    alerts = PredictiveAlert.objects.filter(tenant=tenant).select_related(
        'affected_item', 'affected_vendor', 'created_by',
    )
    status_choices = PredictiveAlert.STATUS_CHOICES
    type_choices = PredictiveAlert.ALERT_TYPE_CHOICES
    severity_choices = PredictiveAlert.SEVERITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        alerts = alerts.filter(
            Q(alert_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        alerts = alerts.filter(status=status_filter)

    type_filter = request.GET.get('alert_type', '').strip()
    if type_filter:
        alerts = alerts.filter(alert_type=type_filter)

    severity_filter = request.GET.get('severity', '').strip()
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)

    return render(request, 'analytics/alert_list.html', {
        'alerts': alerts,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'severity_choices': severity_choices,
        'search_query': search_query,
    })


@login_required
def alert_create_view(request):
    tenant = request.tenant
    form = PredictiveAlertForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        alert = form.save(commit=False)
        alert.tenant = tenant
        alert.created_by = request.user
        alert.save()
        messages.success(request, f'Alert {alert.alert_number} created successfully.')
        return redirect('analytics:alert_detail', pk=alert.pk)

    return render(request, 'analytics/alert_form.html', {
        'form': form,
        'title': 'New Predictive Alert',
    })


@login_required
def alert_detail_view(request, pk):
    tenant = request.tenant
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=tenant)
    return render(request, 'analytics/alert_detail.html', {
        'alert': alert,
    })


@login_required
def alert_edit_view(request, pk):
    tenant = request.tenant
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=tenant, status='new')
    form = PredictiveAlertForm(request.POST or None, instance=alert, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Alert {alert.alert_number} updated successfully.')
        return redirect('analytics:alert_detail', pk=alert.pk)

    return render(request, 'analytics/alert_form.html', {
        'form': form,
        'alert': alert,
        'title': 'Edit Predictive Alert',
    })


@login_required
def alert_delete_view(request, pk):
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=request.tenant, status='new')
    if request.method == 'POST':
        alert.delete()
        messages.success(request, 'Alert deleted successfully.')
        return redirect('analytics:alert_list')
    return redirect('analytics:alert_list')


@login_required
def alert_analyze_view(request, pk):
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=request.tenant, status='new')
    if request.method == 'POST':
        alert.status = 'analyzing'
        alert.save()
        messages.success(request, f'Alert {alert.alert_number} moved to analysis.')
    return redirect('analytics:alert_detail', pk=alert.pk)


@login_required
def alert_confirm_view(request, pk):
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=request.tenant, status='analyzing')
    if request.method == 'POST':
        alert.status = 'confirmed'
        alert.save()
        messages.success(request, f'Alert {alert.alert_number} confirmed.')
    return redirect('analytics:alert_detail', pk=alert.pk)


@login_required
def alert_resolve_view(request, pk):
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=request.tenant, status='confirmed')
    if request.method == 'POST':
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_date = timezone.now().date()
        alert.save()
        messages.success(request, f'Alert {alert.alert_number} resolved.')
    return redirect('analytics:alert_detail', pk=alert.pk)


@login_required
def alert_dismiss_view(request, pk):
    alert = get_object_or_404(PredictiveAlert, pk=pk, tenant=request.tenant)
    if alert.status not in ('new', 'analyzing'):
        return redirect('analytics:alert_detail', pk=alert.pk)
    if request.method == 'POST':
        alert.status = 'dismissed'
        alert.save()
        messages.success(request, f'Alert {alert.alert_number} dismissed.')
    return redirect('analytics:alert_detail', pk=alert.pk)
