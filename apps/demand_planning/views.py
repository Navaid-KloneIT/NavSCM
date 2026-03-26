import math
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CollaborativePlanForm,
    DemandSignalForm,
    ForecastLineItemFormSet,
    PlanCommentForm,
    PlanLineItemFormSet,
    PromotionalEventForm,
    SafetyStockCalculationForm,
    SafetyStockItemFormSet,
    SalesForecastForm,
    SeasonalityProfileForm,
)
from .models import (
    CollaborativePlan,
    DemandSignal,
    PromotionalEvent,
    SafetyStockCalculation,
    SalesForecast,
    SeasonalityProfile,
)


# =============================================================================
# SALES FORECASTING VIEWS
# =============================================================================

@login_required
def forecast_list_view(request):
    tenant = request.tenant
    forecasts = SalesForecast.objects.filter(tenant=tenant).select_related('created_by')
    status_choices = SalesForecast.STATUS_CHOICES
    method_choices = SalesForecast.FORECAST_METHOD_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        forecasts = forecasts.filter(
            Q(forecast_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        forecasts = forecasts.filter(status=status_filter)

    method_filter = request.GET.get('method', '').strip()
    if method_filter:
        forecasts = forecasts.filter(forecast_method=method_filter)

    return render(request, 'demand_planning/forecast_list.html', {
        'forecasts': forecasts,
        'status_choices': status_choices,
        'method_choices': method_choices,
        'search_query': search_query,
    })


@login_required
def forecast_create_view(request):
    tenant = request.tenant
    form = SalesForecastForm(request.POST or None, tenant=tenant)
    formset = ForecastLineItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        forecast = form.save(commit=False)
        forecast.tenant = tenant
        forecast.created_by = request.user
        forecast.save()
        formset.instance = forecast
        formset.save()
        messages.success(request, f'Forecast {forecast.forecast_number} created successfully.')
        return redirect('demand_planning:forecast_detail', pk=forecast.pk)

    return render(request, 'demand_planning/forecast_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Sales Forecast',
    })


@login_required
def forecast_detail_view(request, pk):
    tenant = request.tenant
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=tenant)
    line_items = forecast.items.select_related('item')

    return render(request, 'demand_planning/forecast_detail.html', {
        'forecast': forecast,
        'line_items': line_items,
    })


@login_required
def forecast_edit_view(request, pk):
    tenant = request.tenant
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=tenant, status='draft')
    form = SalesForecastForm(request.POST or None, instance=forecast, tenant=tenant)
    formset = ForecastLineItemFormSet(
        request.POST or None, instance=forecast, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Forecast {forecast.forecast_number} updated successfully.')
        return redirect('demand_planning:forecast_detail', pk=forecast.pk)

    return render(request, 'demand_planning/forecast_form.html', {
        'form': form,
        'formset': formset,
        'forecast': forecast,
        'title': 'Edit Sales Forecast',
    })


@login_required
def forecast_delete_view(request, pk):
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        forecast.delete()
        messages.success(request, 'Forecast deleted successfully.')
        return redirect('demand_planning:forecast_list')
    return redirect('demand_planning:forecast_list')


@login_required
def forecast_submit_view(request, pk):
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        forecast.status = 'submitted'
        forecast.save()
        messages.success(request, f'Forecast {forecast.forecast_number} submitted for approval.')
    return redirect('demand_planning:forecast_detail', pk=forecast.pk)


@login_required
def forecast_approve_view(request, pk):
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=request.tenant, status='submitted')
    if request.method == 'POST':
        forecast.status = 'approved'
        forecast.approved_by = request.user
        forecast.approved_at = timezone.now()
        forecast.save()
        messages.success(request, f'Forecast {forecast.forecast_number} approved.')
    return redirect('demand_planning:forecast_detail', pk=forecast.pk)


@login_required
def forecast_activate_view(request, pk):
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=request.tenant, status='approved')
    if request.method == 'POST':
        forecast.status = 'active'
        forecast.save()
        messages.success(request, f'Forecast {forecast.forecast_number} is now active.')
    return redirect('demand_planning:forecast_detail', pk=forecast.pk)


@login_required
def forecast_archive_view(request, pk):
    forecast = get_object_or_404(SalesForecast, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        forecast.status = 'archived'
        forecast.save()
        messages.success(request, f'Forecast {forecast.forecast_number} archived.')
    return redirect('demand_planning:forecast_detail', pk=forecast.pk)


# =============================================================================
# SEASONALITY PROFILE VIEWS
# =============================================================================

@login_required
def seasonality_list_view(request):
    tenant = request.tenant
    profiles = SeasonalityProfile.objects.filter(tenant=tenant).select_related('item')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        profiles = profiles.filter(
            Q(name__icontains=search_query)
            | Q(item__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        profiles = profiles.filter(is_active=True)
    elif status_filter == 'inactive':
        profiles = profiles.filter(is_active=False)

    return render(request, 'demand_planning/seasonality_list.html', {
        'profiles': profiles,
        'search_query': search_query,
    })


@login_required
def seasonality_create_view(request):
    tenant = request.tenant
    form = SeasonalityProfileForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        profile = form.save(commit=False)
        profile.tenant = tenant
        profile.created_by = request.user
        profile.save()
        messages.success(request, f'Seasonality profile "{profile.name}" created successfully.')
        return redirect('demand_planning:seasonality_detail', pk=profile.pk)

    return render(request, 'demand_planning/seasonality_form.html', {
        'form': form,
        'title': 'New Seasonality Profile',
    })


@login_required
def seasonality_detail_view(request, pk):
    tenant = request.tenant
    profile = get_object_or_404(SeasonalityProfile, pk=pk, tenant=tenant)
    events = profile.events.all()

    return render(request, 'demand_planning/seasonality_detail.html', {
        'profile': profile,
        'events': events,
    })


@login_required
def seasonality_edit_view(request, pk):
    tenant = request.tenant
    profile = get_object_or_404(SeasonalityProfile, pk=pk, tenant=tenant)
    form = SeasonalityProfileForm(request.POST or None, instance=profile, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Seasonality profile "{profile.name}" updated successfully.')
        return redirect('demand_planning:seasonality_detail', pk=profile.pk)

    return render(request, 'demand_planning/seasonality_form.html', {
        'form': form,
        'profile': profile,
        'title': 'Edit Seasonality Profile',
    })


@login_required
def seasonality_delete_view(request, pk):
    profile = get_object_or_404(SeasonalityProfile, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Seasonality profile deleted successfully.')
        return redirect('demand_planning:seasonality_list')
    return redirect('demand_planning:seasonality_list')


# =============================================================================
# PROMOTIONAL EVENT VIEWS
# =============================================================================

@login_required
def event_list_view(request):
    tenant = request.tenant
    events = PromotionalEvent.objects.filter(tenant=tenant).select_related('seasonality_profile')
    type_choices = PromotionalEvent.EVENT_TYPE_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        events = events.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        events = events.filter(event_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        events = events.filter(is_active=True)
    elif status_filter == 'inactive':
        events = events.filter(is_active=False)

    return render(request, 'demand_planning/event_list.html', {
        'events': events,
        'type_choices': type_choices,
        'search_query': search_query,
    })


@login_required
def event_create_view(request):
    tenant = request.tenant
    form = PromotionalEventForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.tenant = tenant
        event.created_by = request.user
        event.save()
        messages.success(request, f'Promotional event "{event.name}" created successfully.')
        return redirect('demand_planning:event_list')

    return render(request, 'demand_planning/event_form.html', {
        'form': form,
        'title': 'New Promotional Event',
    })


@login_required
def event_edit_view(request, pk):
    tenant = request.tenant
    event = get_object_or_404(PromotionalEvent, pk=pk, tenant=tenant)
    form = PromotionalEventForm(request.POST or None, instance=event, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Promotional event "{event.name}" updated successfully.')
        return redirect('demand_planning:event_list')

    return render(request, 'demand_planning/event_form.html', {
        'form': form,
        'event': event,
        'title': 'Edit Promotional Event',
    })


@login_required
def event_delete_view(request, pk):
    event = get_object_or_404(PromotionalEvent, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Promotional event deleted successfully.')
        return redirect('demand_planning:event_list')
    return redirect('demand_planning:event_list')


# =============================================================================
# DEMAND SIGNAL VIEWS
# =============================================================================

@login_required
def signal_list_view(request):
    tenant = request.tenant
    signals = DemandSignal.objects.filter(tenant=tenant).select_related('item', 'created_by')
    type_choices = DemandSignal.SIGNAL_TYPE_CHOICES
    impact_choices = DemandSignal.IMPACT_LEVEL_CHOICES
    status_choices = DemandSignal.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        signals = signals.filter(
            Q(signal_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        signals = signals.filter(signal_type=type_filter)

    impact_filter = request.GET.get('impact', '').strip()
    if impact_filter:
        signals = signals.filter(impact_level=impact_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        signals = signals.filter(status=status_filter)

    return render(request, 'demand_planning/signal_list.html', {
        'signals': signals,
        'type_choices': type_choices,
        'impact_choices': impact_choices,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def signal_create_view(request):
    tenant = request.tenant
    form = DemandSignalForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        signal = form.save(commit=False)
        signal.tenant = tenant
        signal.created_by = request.user
        signal.save()
        messages.success(request, f'Demand signal {signal.signal_number} created successfully.')
        return redirect('demand_planning:signal_detail', pk=signal.pk)

    return render(request, 'demand_planning/signal_form.html', {
        'form': form,
        'title': 'New Demand Signal',
    })


@login_required
def signal_detail_view(request, pk):
    tenant = request.tenant
    signal = get_object_or_404(DemandSignal, pk=pk, tenant=tenant)

    return render(request, 'demand_planning/signal_detail.html', {
        'signal': signal,
    })


@login_required
def signal_edit_view(request, pk):
    tenant = request.tenant
    signal = get_object_or_404(DemandSignal, pk=pk, tenant=tenant, status='new')
    form = DemandSignalForm(request.POST or None, instance=signal, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Demand signal {signal.signal_number} updated successfully.')
        return redirect('demand_planning:signal_detail', pk=signal.pk)

    return render(request, 'demand_planning/signal_form.html', {
        'form': form,
        'signal': signal,
        'title': 'Edit Demand Signal',
    })


@login_required
def signal_delete_view(request, pk):
    signal = get_object_or_404(DemandSignal, pk=pk, tenant=request.tenant, status='new')
    if request.method == 'POST':
        signal.delete()
        messages.success(request, 'Demand signal deleted successfully.')
        return redirect('demand_planning:signal_list')
    return redirect('demand_planning:signal_list')


@login_required
def signal_analyze_view(request, pk):
    signal = get_object_or_404(DemandSignal, pk=pk, tenant=request.tenant, status='new')
    if request.method == 'POST':
        signal.status = 'analyzed'
        signal.analyzed_by = request.user
        signal.analyzed_at = timezone.now()
        signal.save()
        messages.success(request, f'Signal {signal.signal_number} marked as analyzed.')
    return redirect('demand_planning:signal_detail', pk=signal.pk)


@login_required
def signal_incorporate_view(request, pk):
    signal = get_object_or_404(DemandSignal, pk=pk, tenant=request.tenant, status='analyzed')
    if request.method == 'POST':
        signal.status = 'incorporated'
        signal.save()
        messages.success(request, f'Signal {signal.signal_number} incorporated into planning.')
    return redirect('demand_planning:signal_detail', pk=signal.pk)


@login_required
def signal_dismiss_view(request, pk):
    signal = get_object_or_404(
        DemandSignal, pk=pk, tenant=request.tenant,
        status__in=['new', 'analyzed'],
    )
    if request.method == 'POST':
        signal.status = 'dismissed'
        signal.save()
        messages.success(request, f'Signal {signal.signal_number} dismissed.')
    return redirect('demand_planning:signal_detail', pk=signal.pk)


# =============================================================================
# COLLABORATIVE PLAN VIEWS
# =============================================================================

@login_required
def plan_list_view(request):
    tenant = request.tenant
    plans = CollaborativePlan.objects.filter(tenant=tenant).select_related('created_by', 'forecast')
    type_choices = CollaborativePlan.PLAN_TYPE_CHOICES
    status_choices = CollaborativePlan.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        plans = plans.filter(
            Q(plan_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        plans = plans.filter(plan_type=type_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        plans = plans.filter(status=status_filter)

    return render(request, 'demand_planning/plan_list.html', {
        'plans': plans,
        'type_choices': type_choices,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def plan_create_view(request):
    tenant = request.tenant
    form = CollaborativePlanForm(request.POST or None, tenant=tenant)
    formset = PlanLineItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        plan = form.save(commit=False)
        plan.tenant = tenant
        plan.created_by = request.user
        plan.save()
        formset.instance = plan
        formset.save()
        messages.success(request, f'Collaborative plan {plan.plan_number} created successfully.')
        return redirect('demand_planning:plan_detail', pk=plan.pk)

    return render(request, 'demand_planning/plan_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Collaborative Plan',
    })


@login_required
def plan_detail_view(request, pk):
    tenant = request.tenant
    plan = get_object_or_404(CollaborativePlan, pk=pk, tenant=tenant)
    line_items = plan.items.select_related('item')
    comments = plan.comments.select_related('author')
    comment_form = PlanCommentForm()

    return render(request, 'demand_planning/plan_detail.html', {
        'plan': plan,
        'line_items': line_items,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def plan_edit_view(request, pk):
    tenant = request.tenant
    plan = get_object_or_404(CollaborativePlan, pk=pk, tenant=tenant, status='draft')
    form = CollaborativePlanForm(request.POST or None, instance=plan, tenant=tenant)
    formset = PlanLineItemFormSet(
        request.POST or None, instance=plan, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Plan {plan.plan_number} updated successfully.')
        return redirect('demand_planning:plan_detail', pk=plan.pk)

    return render(request, 'demand_planning/plan_form.html', {
        'form': form,
        'formset': formset,
        'plan': plan,
        'title': 'Edit Collaborative Plan',
    })


@login_required
def plan_delete_view(request, pk):
    plan = get_object_or_404(CollaborativePlan, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Collaborative plan deleted successfully.')
        return redirect('demand_planning:plan_list')
    return redirect('demand_planning:plan_list')


@login_required
def plan_submit_view(request, pk):
    plan = get_object_or_404(CollaborativePlan, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        plan.status = 'submitted'
        plan.save()
        messages.success(request, f'Plan {plan.plan_number} submitted for review.')
    return redirect('demand_planning:plan_detail', pk=plan.pk)


@login_required
def plan_approve_view(request, pk):
    plan = get_object_or_404(
        CollaborativePlan, pk=pk, tenant=request.tenant,
        status__in=['submitted', 'review'],
    )
    if request.method == 'POST':
        plan.status = 'approved'
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        messages.success(request, f'Plan {plan.plan_number} approved.')
    return redirect('demand_planning:plan_detail', pk=plan.pk)


@login_required
def plan_finalize_view(request, pk):
    plan = get_object_or_404(CollaborativePlan, pk=pk, tenant=request.tenant, status='approved')
    if request.method == 'POST':
        plan.status = 'finalized'
        plan.save()
        messages.success(request, f'Plan {plan.plan_number} finalized.')
    return redirect('demand_planning:plan_detail', pk=plan.pk)


@login_required
def plan_comment_view(request, pk):
    plan = get_object_or_404(CollaborativePlan, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        form = PlanCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.plan = plan
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added.')
    return redirect('demand_planning:plan_detail', pk=plan.pk)


# =============================================================================
# SAFETY STOCK CALCULATION VIEWS
# =============================================================================

@login_required
def safety_stock_list_view(request):
    tenant = request.tenant
    calculations = SafetyStockCalculation.objects.filter(
        tenant=tenant,
    ).select_related('created_by')
    method_choices = SafetyStockCalculation.CALCULATION_METHOD_CHOICES
    status_choices = SafetyStockCalculation.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        calculations = calculations.filter(
            Q(calculation_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    method_filter = request.GET.get('method', '').strip()
    if method_filter:
        calculations = calculations.filter(calculation_method=method_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        calculations = calculations.filter(status=status_filter)

    return render(request, 'demand_planning/safety_stock_list.html', {
        'calculations': calculations,
        'method_choices': method_choices,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def safety_stock_create_view(request):
    tenant = request.tenant
    form = SafetyStockCalculationForm(request.POST or None, tenant=tenant)
    formset = SafetyStockItemFormSet(
        request.POST or None, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        calc = form.save(commit=False)
        calc.tenant = tenant
        calc.created_by = request.user
        calc.save()
        formset.instance = calc
        formset.save()
        messages.success(request, f'Calculation {calc.calculation_number} created successfully.')
        return redirect('demand_planning:safety_stock_detail', pk=calc.pk)

    return render(request, 'demand_planning/safety_stock_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Safety Stock Calculation',
    })


@login_required
def safety_stock_detail_view(request, pk):
    tenant = request.tenant
    calc = get_object_or_404(SafetyStockCalculation, pk=pk, tenant=tenant)
    items = calc.items.select_related('item', 'warehouse')

    return render(request, 'demand_planning/safety_stock_detail.html', {
        'calc': calc,
        'items': items,
    })


@login_required
def safety_stock_edit_view(request, pk):
    tenant = request.tenant
    calc = get_object_or_404(SafetyStockCalculation, pk=pk, tenant=tenant, status='draft')
    form = SafetyStockCalculationForm(request.POST or None, instance=calc, tenant=tenant)
    formset = SafetyStockItemFormSet(
        request.POST or None, instance=calc, prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Calculation {calc.calculation_number} updated successfully.')
        return redirect('demand_planning:safety_stock_detail', pk=calc.pk)

    return render(request, 'demand_planning/safety_stock_form.html', {
        'form': form,
        'formset': formset,
        'calc': calc,
        'title': 'Edit Safety Stock Calculation',
    })


@login_required
def safety_stock_delete_view(request, pk):
    calc = get_object_or_404(
        SafetyStockCalculation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        calc.delete()
        messages.success(request, 'Safety stock calculation deleted successfully.')
        return redirect('demand_planning:safety_stock_list')
    return redirect('demand_planning:safety_stock_list')


@login_required
def safety_stock_calculate_view(request, pk):
    """Run the safety stock calculation using the Z-score formula."""
    calc = get_object_or_404(
        SafetyStockCalculation, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        # Z-score lookup for common service levels
        z_scores = {
            Decimal('90.00'): Decimal('1.28'),
            Decimal('95.00'): Decimal('1.65'),
            Decimal('97.50'): Decimal('1.96'),
            Decimal('99.00'): Decimal('2.33'),
            Decimal('99.50'): Decimal('2.58'),
            Decimal('99.90'): Decimal('3.09'),
        }

        for item in calc.items.all():
            service_level = item.service_level_pct
            # Find closest Z-score
            z = z_scores.get(service_level)
            if z is None:
                # Approximate: use 1.65 for 95% as default
                z = Decimal('1.65')
                min_diff = None
                for sl, zs in z_scores.items():
                    diff = abs(sl - service_level)
                    if min_diff is None or diff < min_diff:
                        min_diff = diff
                        z = zs

            # Safety Stock = Z * sqrt(LT * σ_d² + d² * σ_LT²)
            lt = Decimal(str(item.lead_time_days))
            d = item.avg_demand
            sigma_d = item.demand_std_dev
            sigma_lt = item.lead_time_std_dev

            under_root = (lt * sigma_d * sigma_d) + (d * d * sigma_lt * sigma_lt)
            safety_stock = z * Decimal(str(math.sqrt(float(under_root))))

            item.calculated_safety_stock = safety_stock.quantize(Decimal('0.01'))
            # Reorder Point = (avg_demand * lead_time) + safety_stock
            item.recommended_reorder_point = (
                (d * lt) + item.calculated_safety_stock
            ).quantize(Decimal('0.01'))
            item.save()

        calc.status = 'calculated'
        calc.save()
        messages.success(request, f'Safety stock calculated for {calc.calculation_number}.')
    return redirect('demand_planning:safety_stock_detail', pk=calc.pk)


@login_required
def safety_stock_approve_view(request, pk):
    calc = get_object_or_404(
        SafetyStockCalculation, pk=pk, tenant=request.tenant, status='calculated',
    )
    if request.method == 'POST':
        calc.status = 'approved'
        calc.approved_by = request.user
        calc.approved_at = timezone.now()
        calc.save()
        messages.success(request, f'Calculation {calc.calculation_number} approved.')
    return redirect('demand_planning:safety_stock_detail', pk=calc.pk)


@login_required
def safety_stock_apply_view(request, pk):
    """Apply calculated safety stock to inventory reorder rules."""
    calc = get_object_or_404(
        SafetyStockCalculation, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        from apps.inventory.models import ReorderRule

        applied_count = 0
        for ss_item in calc.items.all():
            rule = ReorderRule.objects.filter(
                tenant=request.tenant,
                item=ss_item.item,
                warehouse=ss_item.warehouse,
            ).first()
            if rule:
                rule.safety_stock = ss_item.calculated_safety_stock
                rule.reorder_point = ss_item.recommended_reorder_point
                rule.save()
                applied_count += 1

        calc.status = 'applied'
        calc.save()
        messages.success(
            request,
            f'Safety stock applied to {applied_count} reorder rule(s) from {calc.calculation_number}.',
        )
    return redirect('demand_planning:safety_stock_detail', pk=calc.pk)
