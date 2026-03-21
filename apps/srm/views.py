from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.procurement.models import Vendor

from .forms import (
    CatalogItemForm,
    CatalogItemFormSet,
    ContractMilestoneForm,
    ContractMilestoneFormSet,
    DueDiligenceCheckForm,
    DueDiligenceCheckFormSet,
    QualificationQuestionForm,
    QualificationResponseForm,
    QualificationResponseFormSet,
    RiskFactorForm,
    RiskFactorFormSet,
    ScorecardCriteriaForm,
    ScorecardCriteriaFormSet,
    ScorecardPeriodForm,
    SupplierCatalogForm,
    SupplierContractForm,
    SupplierOnboardingForm,
    SupplierRiskAssessmentForm,
    SupplierScorecardForm,
)
from .models import (
    CatalogItem,
    ContractDocument,
    ContractMilestone,
    DueDiligenceCheck,
    QualificationQuestion,
    QualificationResponse,
    RiskFactor,
    RiskMitigationAction,
    ScorecardCriteria,
    ScorecardPeriod,
    SupplierCatalog,
    SupplierContract,
    SupplierOnboarding,
    SupplierRiskAssessment,
    SupplierScorecard,
)


# =============================================================================
# SUPPLIER ONBOARDING VIEWS
# =============================================================================

@login_required
def onboarding_list_view(request):
    tenant = request.tenant
    onboardings = SupplierOnboarding.objects.filter(tenant=tenant).select_related('vendor', 'submitted_by')
    status_choices = SupplierOnboarding.STATUS_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        onboardings = onboardings.filter(
            Q(onboarding_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        onboardings = onboardings.filter(status=status_filter)

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        onboardings = onboardings.filter(vendor_id=vendor_filter)

    return render(request, 'srm/onboarding_list.html', {
        'onboardings': onboardings,
        'status_choices': status_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def onboarding_create_view(request):
    tenant = request.tenant
    form = SupplierOnboardingForm(request.POST or None, tenant=tenant)
    response_formset = QualificationResponseFormSet(
        request.POST or None,
        prefix='responses',
        form_kwargs={'tenant': tenant},
    )
    check_formset = DueDiligenceCheckFormSet(
        request.POST or None,
        prefix='checks',
    )

    if request.method == 'POST' and form.is_valid() and response_formset.is_valid() and check_formset.is_valid():
        onboarding = form.save(commit=False)
        onboarding.tenant = tenant
        onboarding.submitted_by = request.user
        onboarding.save()
        response_formset.instance = onboarding
        response_formset.save()
        check_formset.instance = onboarding
        check_formset.save()
        messages.success(request, f'Onboarding {onboarding.onboarding_number} created successfully.')
        return redirect('srm:onboarding_detail', pk=onboarding.pk)

    return render(request, 'srm/onboarding_form.html', {
        'form': form,
        'response_formset': response_formset,
        'check_formset': check_formset,
        'title': 'Create Supplier Onboarding',
    })


@login_required
def onboarding_detail_view(request, pk):
    tenant = request.tenant
    onboarding = get_object_or_404(
        SupplierOnboarding.objects.select_related('vendor', 'submitted_by', 'reviewed_by'),
        pk=pk,
        tenant=tenant,
    )
    responses = onboarding.responses.select_related('question').all()
    checks = onboarding.due_diligence_checks.all()

    return render(request, 'srm/onboarding_detail.html', {
        'onboarding': onboarding,
        'responses': responses,
        'checks': checks,
    })


@login_required
def onboarding_edit_view(request, pk):
    tenant = request.tenant
    onboarding = get_object_or_404(SupplierOnboarding, pk=pk, tenant=tenant)

    if onboarding.status not in ('draft', 'in_progress'):
        messages.error(request, 'Only draft or in-progress onboardings can be edited.')
        return redirect('srm:onboarding_detail', pk=pk)

    form = SupplierOnboardingForm(request.POST or None, instance=onboarding, tenant=tenant)
    response_formset = QualificationResponseFormSet(
        request.POST or None,
        instance=onboarding,
        prefix='responses',
        form_kwargs={'tenant': tenant},
    )
    check_formset = DueDiligenceCheckFormSet(
        request.POST or None,
        instance=onboarding,
        prefix='checks',
    )

    if request.method == 'POST' and form.is_valid() and response_formset.is_valid() and check_formset.is_valid():
        form.save()
        response_formset.save()
        check_formset.save()
        messages.success(request, f'Onboarding {onboarding.onboarding_number} updated successfully.')
        return redirect('srm:onboarding_detail', pk=onboarding.pk)

    return render(request, 'srm/onboarding_form.html', {
        'form': form,
        'response_formset': response_formset,
        'check_formset': check_formset,
        'title': f'Edit Onboarding {onboarding.onboarding_number}',
        'onboarding': onboarding,
    })


@login_required
def onboarding_delete_view(request, pk):
    tenant = request.tenant
    onboarding = get_object_or_404(SupplierOnboarding, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if onboarding.status != 'draft':
            messages.error(request, 'Only draft onboardings can be deleted.')
            return redirect('srm:onboarding_detail', pk=pk)
        number = onboarding.onboarding_number
        onboarding.delete()
        messages.success(request, f'Onboarding {number} deleted successfully.')
        return redirect('srm:onboarding_list')
    return redirect('srm:onboarding_list')


# =============================================================================
# QUALIFICATION QUESTION VIEWS
# =============================================================================

@login_required
def question_list_view(request):
    tenant = request.tenant
    questions = QualificationQuestion.objects.filter(tenant=tenant)
    category_choices = QualificationQuestion.CATEGORY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        questions = questions.filter(
            Q(question_text__icontains=search_query)
        )

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        questions = questions.filter(category=category_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        questions = questions.filter(is_active=True)
    elif status_filter == 'inactive':
        questions = questions.filter(is_active=False)

    return render(request, 'srm/question_list.html', {
        'questions': questions,
        'category_choices': category_choices,
        'search_query': search_query,
    })


@login_required
def question_create_view(request):
    tenant = request.tenant
    form = QualificationQuestionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.tenant = tenant
        question.save()
        messages.success(request, 'Question created successfully.')
        return redirect('srm:question_list')

    return render(request, 'srm/question_form.html', {
        'form': form,
        'title': 'Add Qualification Question',
    })


@login_required
def question_edit_view(request, pk):
    tenant = request.tenant
    question = get_object_or_404(QualificationQuestion, pk=pk, tenant=tenant)
    form = QualificationQuestionForm(request.POST or None, instance=question)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Question updated successfully.')
        return redirect('srm:question_list')

    return render(request, 'srm/question_form.html', {
        'form': form,
        'title': 'Edit Qualification Question',
        'question': question,
    })


@login_required
def question_delete_view(request, pk):
    tenant = request.tenant
    question = get_object_or_404(QualificationQuestion, pk=pk, tenant=tenant)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('srm:question_list')
    return redirect('srm:question_list')


# =============================================================================
# SCORECARD PERIOD VIEWS
# =============================================================================

@login_required
def period_list_view(request):
    tenant = request.tenant
    periods = ScorecardPeriod.objects.filter(tenant=tenant)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        periods = periods.filter(
            Q(name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        periods = periods.filter(is_active=True)
    elif status_filter == 'inactive':
        periods = periods.filter(is_active=False)

    return render(request, 'srm/period_list.html', {
        'periods': periods,
        'search_query': search_query,
    })


@login_required
def period_create_view(request):
    tenant = request.tenant
    form = ScorecardPeriodForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        period = form.save(commit=False)
        period.tenant = tenant
        period.save()
        messages.success(request, f'Period "{period.name}" created successfully.')
        return redirect('srm:period_list')

    return render(request, 'srm/period_form.html', {
        'form': form,
        'title': 'Add Scorecard Period',
    })


@login_required
def period_edit_view(request, pk):
    tenant = request.tenant
    period = get_object_or_404(ScorecardPeriod, pk=pk, tenant=tenant)
    form = ScorecardPeriodForm(request.POST or None, instance=period)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Period "{period.name}" updated successfully.')
        return redirect('srm:period_list')

    return render(request, 'srm/period_form.html', {
        'form': form,
        'title': 'Edit Scorecard Period',
        'period': period,
    })


@login_required
def period_delete_view(request, pk):
    tenant = request.tenant
    period = get_object_or_404(ScorecardPeriod, pk=pk, tenant=tenant)
    if request.method == 'POST':
        name = period.name
        period.delete()
        messages.success(request, f'Period "{name}" deleted successfully.')
        return redirect('srm:period_list')
    return redirect('srm:period_list')


# =============================================================================
# SUPPLIER SCORECARD VIEWS
# =============================================================================

@login_required
def scorecard_list_view(request):
    tenant = request.tenant
    scorecards = SupplierScorecard.objects.filter(tenant=tenant).select_related('vendor', 'period', 'evaluated_by')
    status_choices = SupplierScorecard.STATUS_CHOICES
    rating_choices = SupplierScorecard.RATING_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        scorecards = scorecards.filter(
            Q(scorecard_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        scorecards = scorecards.filter(status=status_filter)

    rating_filter = request.GET.get('rating', '').strip()
    if rating_filter:
        scorecards = scorecards.filter(rating=rating_filter)

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        scorecards = scorecards.filter(vendor_id=vendor_filter)

    return render(request, 'srm/scorecard_list.html', {
        'scorecards': scorecards,
        'status_choices': status_choices,
        'rating_choices': rating_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def scorecard_create_view(request):
    tenant = request.tenant
    form = SupplierScorecardForm(request.POST or None, tenant=tenant)
    formset = ScorecardCriteriaFormSet(
        request.POST or None,
        prefix='criteria',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        scorecard = form.save(commit=False)
        scorecard.tenant = tenant
        scorecard.evaluated_by = request.user
        scorecard.save()
        formset.instance = scorecard
        formset.save()
        messages.success(request, f'Scorecard {scorecard.scorecard_number} created successfully.')
        return redirect('srm:scorecard_detail', pk=scorecard.pk)

    return render(request, 'srm/scorecard_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Supplier Scorecard',
    })


@login_required
def scorecard_detail_view(request, pk):
    tenant = request.tenant
    scorecard = get_object_or_404(
        SupplierScorecard.objects.select_related('vendor', 'period', 'evaluated_by', 'approved_by'),
        pk=pk,
        tenant=tenant,
    )
    criteria = scorecard.criteria.all()

    return render(request, 'srm/scorecard_detail.html', {
        'scorecard': scorecard,
        'criteria': criteria,
    })


@login_required
def scorecard_edit_view(request, pk):
    tenant = request.tenant
    scorecard = get_object_or_404(SupplierScorecard, pk=pk, tenant=tenant)

    if scorecard.status != 'draft':
        messages.error(request, 'Only draft scorecards can be edited.')
        return redirect('srm:scorecard_detail', pk=pk)

    form = SupplierScorecardForm(request.POST or None, instance=scorecard, tenant=tenant)
    formset = ScorecardCriteriaFormSet(
        request.POST or None,
        instance=scorecard,
        prefix='criteria',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Scorecard {scorecard.scorecard_number} updated successfully.')
        return redirect('srm:scorecard_detail', pk=scorecard.pk)

    return render(request, 'srm/scorecard_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Scorecard {scorecard.scorecard_number}',
        'scorecard': scorecard,
    })


@login_required
def scorecard_delete_view(request, pk):
    tenant = request.tenant
    scorecard = get_object_or_404(SupplierScorecard, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if scorecard.status != 'draft':
            messages.error(request, 'Only draft scorecards can be deleted.')
            return redirect('srm:scorecard_detail', pk=pk)
        number = scorecard.scorecard_number
        scorecard.delete()
        messages.success(request, f'Scorecard {number} deleted successfully.')
        return redirect('srm:scorecard_list')
    return redirect('srm:scorecard_list')


# =============================================================================
# SUPPLIER CONTRACT VIEWS
# =============================================================================

@login_required
def contract_list_view(request):
    tenant = request.tenant
    contracts = SupplierContract.objects.filter(tenant=tenant).select_related('vendor', 'created_by')
    status_choices = SupplierContract.STATUS_CHOICES
    type_choices = SupplierContract.TYPE_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

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

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        contracts = contracts.filter(vendor_id=vendor_filter)

    return render(request, 'srm/contract_list.html', {
        'contracts': contracts,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def contract_create_view(request):
    tenant = request.tenant
    form = SupplierContractForm(request.POST or None, tenant=tenant)
    formset = ContractMilestoneFormSet(
        request.POST or None,
        prefix='milestones',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        contract = form.save(commit=False)
        contract.tenant = tenant
        contract.created_by = request.user
        contract.save()
        formset.instance = contract
        formset.save()
        messages.success(request, f'Contract {contract.contract_number} created successfully.')
        return redirect('srm:contract_detail', pk=contract.pk)

    return render(request, 'srm/contract_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Supplier Contract',
    })


@login_required
def contract_detail_view(request, pk):
    tenant = request.tenant
    contract = get_object_or_404(
        SupplierContract.objects.select_related('vendor', 'created_by', 'approved_by'),
        pk=pk,
        tenant=tenant,
    )
    milestones = contract.milestones.all()
    documents = contract.documents.select_related('uploaded_by').all()

    return render(request, 'srm/contract_detail.html', {
        'contract': contract,
        'milestones': milestones,
        'documents': documents,
    })


@login_required
def contract_edit_view(request, pk):
    tenant = request.tenant
    contract = get_object_or_404(SupplierContract, pk=pk, tenant=tenant)

    if contract.status != 'draft':
        messages.error(request, 'Only draft contracts can be edited.')
        return redirect('srm:contract_detail', pk=pk)

    form = SupplierContractForm(request.POST or None, instance=contract, tenant=tenant)
    formset = ContractMilestoneFormSet(
        request.POST or None,
        instance=contract,
        prefix='milestones',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Contract {contract.contract_number} updated successfully.')
        return redirect('srm:contract_detail', pk=contract.pk)

    return render(request, 'srm/contract_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Contract {contract.contract_number}',
        'contract': contract,
    })


@login_required
def contract_delete_view(request, pk):
    tenant = request.tenant
    contract = get_object_or_404(SupplierContract, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if contract.status != 'draft':
            messages.error(request, 'Only draft contracts can be deleted.')
            return redirect('srm:contract_detail', pk=pk)
        number = contract.contract_number
        contract.delete()
        messages.success(request, f'Contract {number} deleted successfully.')
        return redirect('srm:contract_list')
    return redirect('srm:contract_list')


# =============================================================================
# SUPPLIER CATALOG VIEWS
# =============================================================================

@login_required
def catalog_list_view(request):
    tenant = request.tenant
    catalogs = SupplierCatalog.objects.filter(tenant=tenant).select_related('vendor', 'created_by')
    status_choices = SupplierCatalog.STATUS_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        catalogs = catalogs.filter(
            Q(catalog_number__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        catalogs = catalogs.filter(status=status_filter)

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        catalogs = catalogs.filter(vendor_id=vendor_filter)

    return render(request, 'srm/catalog_list.html', {
        'catalogs': catalogs,
        'status_choices': status_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def catalog_create_view(request):
    tenant = request.tenant
    form = SupplierCatalogForm(request.POST or None, tenant=tenant)
    formset = CatalogItemFormSet(
        request.POST or None,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        catalog = form.save(commit=False)
        catalog.tenant = tenant
        catalog.created_by = request.user
        catalog.save()
        formset.instance = catalog
        formset.save()
        messages.success(request, f'Catalog {catalog.catalog_number} created successfully.')
        return redirect('srm:catalog_detail', pk=catalog.pk)

    return render(request, 'srm/catalog_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Supplier Catalog',
    })


@login_required
def catalog_detail_view(request, pk):
    tenant = request.tenant
    catalog = get_object_or_404(
        SupplierCatalog.objects.select_related('vendor', 'created_by'),
        pk=pk,
        tenant=tenant,
    )
    items = catalog.items.select_related('item').all()

    return render(request, 'srm/catalog_detail.html', {
        'catalog': catalog,
        'items': items,
    })


@login_required
def catalog_edit_view(request, pk):
    tenant = request.tenant
    catalog = get_object_or_404(SupplierCatalog, pk=pk, tenant=tenant)

    if catalog.status != 'draft':
        messages.error(request, 'Only draft catalogs can be edited.')
        return redirect('srm:catalog_detail', pk=pk)

    form = SupplierCatalogForm(request.POST or None, instance=catalog, tenant=tenant)
    formset = CatalogItemFormSet(
        request.POST or None,
        instance=catalog,
        prefix='items',
        form_kwargs={'tenant': tenant},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Catalog {catalog.catalog_number} updated successfully.')
        return redirect('srm:catalog_detail', pk=catalog.pk)

    return render(request, 'srm/catalog_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Catalog {catalog.catalog_number}',
        'catalog': catalog,
    })


@login_required
def catalog_delete_view(request, pk):
    tenant = request.tenant
    catalog = get_object_or_404(SupplierCatalog, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if catalog.status != 'draft':
            messages.error(request, 'Only draft catalogs can be deleted.')
            return redirect('srm:catalog_detail', pk=pk)
        number = catalog.catalog_number
        catalog.delete()
        messages.success(request, f'Catalog {number} deleted successfully.')
        return redirect('srm:catalog_list')
    return redirect('srm:catalog_list')


# =============================================================================
# SUPPLIER RISK ASSESSMENT VIEWS
# =============================================================================

@login_required
def risk_list_view(request):
    tenant = request.tenant
    assessments = SupplierRiskAssessment.objects.filter(tenant=tenant).select_related('vendor', 'assessed_by')
    status_choices = SupplierRiskAssessment.STATUS_CHOICES
    risk_level_choices = SupplierRiskAssessment.RISK_LEVEL_CHOICES
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        assessments = assessments.filter(
            Q(assessment_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        assessments = assessments.filter(status=status_filter)

    risk_level_filter = request.GET.get('risk_level', '').strip()
    if risk_level_filter:
        assessments = assessments.filter(overall_risk_level=risk_level_filter)

    vendor_filter = request.GET.get('vendor', '').strip()
    if vendor_filter:
        assessments = assessments.filter(vendor_id=vendor_filter)

    return render(request, 'srm/risk_list.html', {
        'assessments': assessments,
        'status_choices': status_choices,
        'risk_level_choices': risk_level_choices,
        'vendors': vendors,
        'search_query': search_query,
    })


@login_required
def risk_create_view(request):
    tenant = request.tenant
    form = SupplierRiskAssessmentForm(request.POST or None, tenant=tenant)
    formset = RiskFactorFormSet(
        request.POST or None,
        prefix='factors',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        assessment = form.save(commit=False)
        assessment.tenant = tenant
        assessment.assessed_by = request.user
        assessment.save()
        formset.instance = assessment
        formset.save()
        messages.success(request, f'Risk Assessment {assessment.assessment_number} created successfully.')
        return redirect('srm:risk_detail', pk=assessment.pk)

    return render(request, 'srm/risk_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Risk Assessment',
    })


@login_required
def risk_detail_view(request, pk):
    tenant = request.tenant
    assessment = get_object_or_404(
        SupplierRiskAssessment.objects.select_related('vendor', 'assessed_by', 'reviewed_by'),
        pk=pk,
        tenant=tenant,
    )
    risk_factors = assessment.risk_factors.prefetch_related('mitigation_actions').all()

    return render(request, 'srm/risk_detail.html', {
        'assessment': assessment,
        'risk_factors': risk_factors,
    })


@login_required
def risk_edit_view(request, pk):
    tenant = request.tenant
    assessment = get_object_or_404(SupplierRiskAssessment, pk=pk, tenant=tenant)

    if assessment.status not in ('draft', 'in_progress'):
        messages.error(request, 'Only draft or in-progress assessments can be edited.')
        return redirect('srm:risk_detail', pk=pk)

    form = SupplierRiskAssessmentForm(request.POST or None, instance=assessment, tenant=tenant)
    formset = RiskFactorFormSet(
        request.POST or None,
        instance=assessment,
        prefix='factors',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Risk Assessment {assessment.assessment_number} updated successfully.')
        return redirect('srm:risk_detail', pk=assessment.pk)

    return render(request, 'srm/risk_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Risk Assessment {assessment.assessment_number}',
        'assessment': assessment,
    })


@login_required
def risk_delete_view(request, pk):
    tenant = request.tenant
    assessment = get_object_or_404(SupplierRiskAssessment, pk=pk, tenant=tenant)
    if request.method == 'POST':
        if assessment.status != 'draft':
            messages.error(request, 'Only draft assessments can be deleted.')
            return redirect('srm:risk_detail', pk=pk)
        number = assessment.assessment_number
        assessment.delete()
        messages.success(request, f'Risk Assessment {number} deleted successfully.')
        return redirect('srm:risk_list')
    return redirect('srm:risk_list')
