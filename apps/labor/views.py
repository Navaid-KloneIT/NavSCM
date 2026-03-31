from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AttendanceForm,
    LaborPlanForm,
    LaborPlanLineFormSet,
    PayrollRecordForm,
    PerformanceReviewForm,
    TaskAssignmentForm,
    TaskChecklistItemFormSet,
)
from .models import (
    Attendance,
    LaborPlan,
    PayrollRecord,
    PerformanceReview,
    TaskAssignment,
)


# =============================================================================
# LABOR PLANNING VIEWS
# =============================================================================

@login_required
def plan_list_view(request):
    tenant = request.tenant
    plans = LaborPlan.objects.filter(tenant=tenant).select_related(
        'warehouse', 'created_by',
    )
    status_choices = LaborPlan.STATUS_CHOICES
    department_choices = LaborPlan.DEPARTMENT_CHOICES
    shift_choices = LaborPlan.SHIFT_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        plans = plans.filter(
            Q(plan_number__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        plans = plans.filter(status=status_filter)

    department_filter = request.GET.get('department', '').strip()
    if department_filter:
        plans = plans.filter(department=department_filter)

    shift_filter = request.GET.get('shift', '').strip()
    if shift_filter:
        plans = plans.filter(shift=shift_filter)

    return render(request, 'labor/plan_list.html', {
        'plans': plans,
        'status_choices': status_choices,
        'department_choices': department_choices,
        'shift_choices': shift_choices,
        'search_query': search_query,
    })


@login_required
def plan_create_view(request):
    tenant = request.tenant
    form = LaborPlanForm(request.POST or None, tenant=tenant)
    formset = LaborPlanLineFormSet(request.POST or None, prefix='lines')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        plan = form.save(commit=False)
        plan.tenant = tenant
        plan.created_by = request.user
        plan.save()
        formset.instance = plan
        formset.save()
        messages.success(request, f'Labor Plan {plan.plan_number} created successfully.')
        return redirect('labor:plan_detail', pk=plan.pk)

    return render(request, 'labor/plan_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Labor Plan',
    })


@login_required
def plan_detail_view(request, pk):
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=request.tenant)
    lines = plan.plan_lines.all()

    return render(request, 'labor/plan_detail.html', {
        'plan': plan,
        'lines': lines,
    })


@login_required
def plan_edit_view(request, pk):
    tenant = request.tenant
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=tenant, status='draft')
    form = LaborPlanForm(request.POST or None, instance=plan, tenant=tenant)
    formset = LaborPlanLineFormSet(
        request.POST or None, instance=plan, prefix='lines',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Labor Plan {plan.plan_number} updated successfully.')
        return redirect('labor:plan_detail', pk=plan.pk)

    return render(request, 'labor/plan_form.html', {
        'form': form,
        'formset': formset,
        'plan': plan,
        'title': 'Edit Labor Plan',
    })


@login_required
def plan_delete_view(request, pk):
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Labor Plan deleted successfully.')
        return redirect('labor:plan_list')
    return redirect('labor:plan_list')


@login_required
def plan_approve_view(request, pk):
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=request.tenant, status='draft')
    if request.method == 'POST':
        plan.status = 'approved'
        plan.save()
        messages.success(request, f'Labor Plan {plan.plan_number} approved.')
    return redirect('labor:plan_detail', pk=plan.pk)


@login_required
def plan_activate_view(request, pk):
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=request.tenant, status='approved')
    if request.method == 'POST':
        plan.status = 'active'
        plan.save()
        messages.success(request, f'Labor Plan {plan.plan_number} activated.')
    return redirect('labor:plan_detail', pk=plan.pk)


@login_required
def plan_complete_view(request, pk):
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=request.tenant, status='active')
    if request.method == 'POST':
        plan.status = 'completed'
        plan.save()
        messages.success(request, f'Labor Plan {plan.plan_number} completed.')
    return redirect('labor:plan_detail', pk=plan.pk)


@login_required
def plan_cancel_view(request, pk):
    plan = get_object_or_404(LaborPlan, pk=pk, tenant=request.tenant)
    if plan.status in ('completed', 'cancelled'):
        return redirect('labor:plan_detail', pk=plan.pk)
    if request.method == 'POST':
        plan.status = 'cancelled'
        plan.save()
        messages.warning(request, f'Labor Plan {plan.plan_number} cancelled.')
    return redirect('labor:plan_detail', pk=plan.pk)


# =============================================================================
# TIME & ATTENDANCE VIEWS
# =============================================================================

@login_required
def attendance_list_view(request):
    tenant = request.tenant
    records = Attendance.objects.filter(tenant=tenant).select_related(
        'worker', 'warehouse', 'created_by',
    )
    status_choices = Attendance.STATUS_CHOICES
    shift_choices = Attendance.SHIFT_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        records = records.filter(
            Q(attendance_number__icontains=search_query)
            | Q(worker__username__icontains=search_query)
            | Q(worker__first_name__icontains=search_query)
            | Q(worker__last_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        records = records.filter(status=status_filter)

    shift_filter = request.GET.get('shift', '').strip()
    if shift_filter:
        records = records.filter(shift=shift_filter)

    return render(request, 'labor/attendance_list.html', {
        'records': records,
        'status_choices': status_choices,
        'shift_choices': shift_choices,
        'search_query': search_query,
    })


@login_required
def attendance_create_view(request):
    tenant = request.tenant
    form = AttendanceForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.tenant = tenant
        record.created_by = request.user
        record.save()
        messages.success(request, f'Attendance {record.attendance_number} created successfully.')
        return redirect('labor:attendance_detail', pk=record.pk)

    return render(request, 'labor/attendance_form.html', {
        'form': form,
        'title': 'New Attendance Record',
    })


@login_required
def attendance_detail_view(request, pk):
    record = get_object_or_404(Attendance, pk=pk, tenant=request.tenant)

    return render(request, 'labor/attendance_detail.html', {
        'record': record,
    })


@login_required
def attendance_edit_view(request, pk):
    tenant = request.tenant
    record = get_object_or_404(Attendance, pk=pk, tenant=tenant, status='clocked_in')
    form = AttendanceForm(request.POST or None, instance=record, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Attendance {record.attendance_number} updated successfully.')
        return redirect('labor:attendance_detail', pk=record.pk)

    return render(request, 'labor/attendance_form.html', {
        'form': form,
        'record': record,
        'title': 'Edit Attendance Record',
    })


@login_required
def attendance_delete_view(request, pk):
    record = get_object_or_404(
        Attendance, pk=pk, tenant=request.tenant, status='clocked_in',
    )
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Attendance record deleted successfully.')
        return redirect('labor:attendance_list')
    return redirect('labor:attendance_list')


@login_required
def attendance_clock_out_view(request, pk):
    record = get_object_or_404(Attendance, pk=pk, tenant=request.tenant)
    if record.status not in ('clocked_in', 'on_break'):
        return redirect('labor:attendance_detail', pk=record.pk)
    if request.method == 'POST':
        record.status = 'clocked_out'
        record.clock_out = timezone.now()
        record.save()
        messages.success(request, f'Attendance {record.attendance_number} clocked out.')
    return redirect('labor:attendance_detail', pk=record.pk)


@login_required
def attendance_approve_view(request, pk):
    record = get_object_or_404(
        Attendance, pk=pk, tenant=request.tenant, status='clocked_out',
    )
    if request.method == 'POST':
        record.status = 'approved'
        record.save()
        messages.success(request, f'Attendance {record.attendance_number} approved.')
    return redirect('labor:attendance_detail', pk=record.pk)


@login_required
def attendance_lock_view(request, pk):
    record = get_object_or_404(
        Attendance, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        record.status = 'locked'
        record.save()
        messages.info(request, f'Attendance {record.attendance_number} locked.')
    return redirect('labor:attendance_detail', pk=record.pk)


# =============================================================================
# TASK ASSIGNMENT VIEWS
# =============================================================================

@login_required
def task_list_view(request):
    tenant = request.tenant
    tasks = TaskAssignment.objects.filter(tenant=tenant).select_related(
        'warehouse', 'assigned_to', 'created_by',
    )
    status_choices = TaskAssignment.STATUS_CHOICES
    type_choices = TaskAssignment.TASK_TYPE_CHOICES
    priority_choices = TaskAssignment.PRIORITY_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tasks = tasks.filter(
            Q(task_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(assigned_to__username__icontains=search_query)
            | Q(assigned_to__first_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    type_filter = request.GET.get('task_type', '').strip()
    if type_filter:
        tasks = tasks.filter(task_type=type_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    return render(request, 'labor/task_list.html', {
        'tasks': tasks,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
    })


@login_required
def task_create_view(request):
    tenant = request.tenant
    form = TaskAssignmentForm(request.POST or None, tenant=tenant)
    formset = TaskChecklistItemFormSet(request.POST or None, prefix='checklist')

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        task = form.save(commit=False)
        task.tenant = tenant
        task.created_by = request.user
        task.save()
        formset.instance = task
        formset.save()
        messages.success(request, f'Task {task.task_number} created successfully.')
        return redirect('labor:task_detail', pk=task.pk)

    return render(request, 'labor/task_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Task Assignment',
    })


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(TaskAssignment, pk=pk, tenant=request.tenant)
    checklist = task.checklist_items.all()

    return render(request, 'labor/task_detail.html', {
        'task': task,
        'checklist': checklist,
    })


@login_required
def task_edit_view(request, pk):
    tenant = request.tenant
    task = get_object_or_404(TaskAssignment, pk=pk, tenant=tenant, status='pending')
    form = TaskAssignmentForm(request.POST or None, instance=task, tenant=tenant)
    formset = TaskChecklistItemFormSet(
        request.POST or None, instance=task, prefix='checklist',
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, f'Task {task.task_number} updated successfully.')
        return redirect('labor:task_detail', pk=task.pk)

    return render(request, 'labor/task_form.html', {
        'form': form,
        'formset': formset,
        'task': task,
        'title': 'Edit Task Assignment',
    })


@login_required
def task_delete_view(request, pk):
    task = get_object_or_404(
        TaskAssignment, pk=pk, tenant=request.tenant, status='pending',
    )
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('labor:task_list')
    return redirect('labor:task_list')


@login_required
def task_assign_view(request, pk):
    task = get_object_or_404(
        TaskAssignment, pk=pk, tenant=request.tenant, status='pending',
    )
    if request.method == 'POST':
        task.status = 'assigned'
        if not task.assigned_date:
            task.assigned_date = timezone.now().date()
        task.save()
        messages.success(request, f'Task {task.task_number} assigned.')
    return redirect('labor:task_detail', pk=task.pk)


@login_required
def task_start_view(request, pk):
    task = get_object_or_404(
        TaskAssignment, pk=pk, tenant=request.tenant, status='assigned',
    )
    if request.method == 'POST':
        task.status = 'in_progress'
        task.started_at = timezone.now()
        task.save()
        messages.success(request, f'Task {task.task_number} started.')
    return redirect('labor:task_detail', pk=task.pk)


@login_required
def task_complete_view(request, pk):
    task = get_object_or_404(
        TaskAssignment, pk=pk, tenant=request.tenant, status='in_progress',
    )
    if request.method == 'POST':
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        messages.success(request, f'Task {task.task_number} completed.')
    return redirect('labor:task_detail', pk=task.pk)


@login_required
def task_cancel_view(request, pk):
    task = get_object_or_404(TaskAssignment, pk=pk, tenant=request.tenant)
    if task.status in ('completed', 'cancelled'):
        return redirect('labor:task_detail', pk=task.pk)
    if request.method == 'POST':
        task.status = 'cancelled'
        task.save()
        messages.warning(request, f'Task {task.task_number} cancelled.')
    return redirect('labor:task_detail', pk=task.pk)


# =============================================================================
# PERFORMANCE TRACKING VIEWS
# =============================================================================

@login_required
def performance_list_view(request):
    tenant = request.tenant
    reviews = PerformanceReview.objects.filter(tenant=tenant).select_related(
        'worker', 'warehouse', 'reviewed_by', 'created_by',
    )
    status_choices = PerformanceReview.STATUS_CHOICES
    rating_choices = PerformanceReview.RATING_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reviews = reviews.filter(
            Q(review_number__icontains=search_query)
            | Q(worker__username__icontains=search_query)
            | Q(worker__first_name__icontains=search_query)
            | Q(worker__last_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        reviews = reviews.filter(status=status_filter)

    rating_filter = request.GET.get('rating', '').strip()
    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)

    return render(request, 'labor/performance_list.html', {
        'reviews': reviews,
        'status_choices': status_choices,
        'rating_choices': rating_choices,
        'search_query': search_query,
    })


@login_required
def performance_create_view(request):
    tenant = request.tenant
    form = PerformanceReviewForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.tenant = tenant
        review.created_by = request.user
        review.save()
        messages.success(request, f'Performance Review {review.review_number} created successfully.')
        return redirect('labor:performance_detail', pk=review.pk)

    return render(request, 'labor/performance_form.html', {
        'form': form,
        'title': 'New Performance Review',
    })


@login_required
def performance_detail_view(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk, tenant=request.tenant)

    return render(request, 'labor/performance_detail.html', {
        'review': review,
    })


@login_required
def performance_edit_view(request, pk):
    tenant = request.tenant
    review = get_object_or_404(
        PerformanceReview, pk=pk, tenant=tenant, status='draft',
    )
    form = PerformanceReviewForm(request.POST or None, instance=review, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Performance Review {review.review_number} updated successfully.')
        return redirect('labor:performance_detail', pk=review.pk)

    return render(request, 'labor/performance_form.html', {
        'form': form,
        'review': review,
        'title': 'Edit Performance Review',
    })


@login_required
def performance_delete_view(request, pk):
    review = get_object_or_404(
        PerformanceReview, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Performance Review deleted successfully.')
        return redirect('labor:performance_list')
    return redirect('labor:performance_list')


@login_required
def performance_submit_view(request, pk):
    review = get_object_or_404(
        PerformanceReview, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        review.status = 'submitted'
        review.save()
        messages.success(request, f'Performance Review {review.review_number} submitted.')
    return redirect('labor:performance_detail', pk=review.pk)


@login_required
def performance_approve_view(request, pk):
    review = get_object_or_404(
        PerformanceReview, pk=pk, tenant=request.tenant, status='submitted',
    )
    if request.method == 'POST':
        review.status = 'approved'
        review.save()
        messages.success(request, f'Performance Review {review.review_number} approved.')
    return redirect('labor:performance_detail', pk=review.pk)


@login_required
def performance_close_view(request, pk):
    review = get_object_or_404(
        PerformanceReview, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        review.status = 'closed'
        review.save()
        messages.info(request, f'Performance Review {review.review_number} closed.')
    return redirect('labor:performance_detail', pk=review.pk)


@login_required
def performance_cancel_view(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk, tenant=request.tenant)
    if review.status in ('closed', 'cancelled'):
        return redirect('labor:performance_detail', pk=review.pk)
    if request.method == 'POST':
        review.status = 'cancelled'
        review.save()
        messages.warning(request, f'Performance Review {review.review_number} cancelled.')
    return redirect('labor:performance_detail', pk=review.pk)


# =============================================================================
# PAYROLL INTEGRATION VIEWS
# =============================================================================

@login_required
def payroll_list_view(request):
    tenant = request.tenant
    records = PayrollRecord.objects.filter(tenant=tenant).select_related(
        'worker', 'created_by',
    )
    status_choices = PayrollRecord.STATUS_CHOICES

    search_query = request.GET.get('q', '').strip()
    if search_query:
        records = records.filter(
            Q(payroll_number__icontains=search_query)
            | Q(worker__username__icontains=search_query)
            | Q(worker__first_name__icontains=search_query)
            | Q(worker__last_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        records = records.filter(status=status_filter)

    return render(request, 'labor/payroll_list.html', {
        'records': records,
        'status_choices': status_choices,
        'search_query': search_query,
    })


@login_required
def payroll_create_view(request):
    tenant = request.tenant
    form = PayrollRecordForm(request.POST or None, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.tenant = tenant
        record.created_by = request.user
        record.save()
        messages.success(request, f'Payroll {record.payroll_number} created successfully.')
        return redirect('labor:payroll_detail', pk=record.pk)

    return render(request, 'labor/payroll_form.html', {
        'form': form,
        'title': 'New Payroll Record',
    })


@login_required
def payroll_detail_view(request, pk):
    record = get_object_or_404(PayrollRecord, pk=pk, tenant=request.tenant)

    return render(request, 'labor/payroll_detail.html', {
        'record': record,
    })


@login_required
def payroll_edit_view(request, pk):
    tenant = request.tenant
    record = get_object_or_404(
        PayrollRecord, pk=pk, tenant=tenant, status='draft',
    )
    form = PayrollRecordForm(request.POST or None, instance=record, tenant=tenant)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Payroll {record.payroll_number} updated successfully.')
        return redirect('labor:payroll_detail', pk=record.pk)

    return render(request, 'labor/payroll_form.html', {
        'form': form,
        'record': record,
        'title': 'Edit Payroll Record',
    })


@login_required
def payroll_delete_view(request, pk):
    record = get_object_or_404(
        PayrollRecord, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Payroll record deleted successfully.')
        return redirect('labor:payroll_list')
    return redirect('labor:payroll_list')


@login_required
def payroll_calculate_view(request, pk):
    record = get_object_or_404(
        PayrollRecord, pk=pk, tenant=request.tenant, status='draft',
    )
    if request.method == 'POST':
        record.status = 'calculated'
        record.save()
        messages.success(request, f'Payroll {record.payroll_number} calculated.')
    return redirect('labor:payroll_detail', pk=record.pk)


@login_required
def payroll_approve_view(request, pk):
    record = get_object_or_404(
        PayrollRecord, pk=pk, tenant=request.tenant, status='calculated',
    )
    if request.method == 'POST':
        record.status = 'approved'
        record.save()
        messages.success(request, f'Payroll {record.payroll_number} approved.')
    return redirect('labor:payroll_detail', pk=record.pk)


@login_required
def payroll_export_view(request, pk):
    record = get_object_or_404(
        PayrollRecord, pk=pk, tenant=request.tenant, status='approved',
    )
    if request.method == 'POST':
        record.status = 'exported'
        record.exported_at = timezone.now()
        record.save()
        messages.success(request, f'Payroll {record.payroll_number} exported.')
    return redirect('labor:payroll_detail', pk=record.pk)


@login_required
def payroll_cancel_view(request, pk):
    record = get_object_or_404(PayrollRecord, pk=pk, tenant=request.tenant)
    if record.status in ('exported', 'cancelled'):
        return redirect('labor:payroll_detail', pk=record.pk)
    if request.method == 'POST':
        record.status = 'cancelled'
        record.save()
        messages.warning(request, f'Payroll {record.payroll_number} cancelled.')
    return redirect('labor:payroll_detail', pk=record.pk)
