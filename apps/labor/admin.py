from django.contrib import admin

from .models import (
    Attendance,
    LaborPlan,
    LaborPlanLine,
    PayrollRecord,
    PerformanceReview,
    TaskAssignment,
    TaskChecklistItem,
)


# Inlines
class LaborPlanLineInline(admin.TabularInline):
    model = LaborPlanLine
    extra = 1


class TaskChecklistItemInline(admin.TabularInline):
    model = TaskChecklistItem
    extra = 1


# Main Admins
@admin.register(LaborPlan)
class LaborPlanAdmin(admin.ModelAdmin):
    list_display = (
        'plan_number', 'title', 'department', 'shift', 'status',
        'required_headcount', 'available_headcount', 'plan_date',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'department', 'shift', 'tenant')
    search_fields = ('plan_number', 'title')
    inlines = [LaborPlanLineInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'attendance_number', 'worker', 'date', 'shift', 'status',
        'clock_in', 'clock_out', 'tenant', 'created_at',
    )
    list_filter = ('status', 'shift', 'tenant')
    search_fields = ('attendance_number', 'worker__username', 'worker__first_name')


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'task_number', 'title', 'task_type', 'priority', 'status',
        'assigned_to', 'due_date', 'tenant', 'created_at',
    )
    list_filter = ('status', 'task_type', 'priority', 'tenant')
    search_fields = ('task_number', 'title', 'assigned_to__username')
    inlines = [TaskChecklistItemInline]


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = (
        'review_number', 'worker', 'period_start', 'period_end',
        'rating', 'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'rating', 'tenant')
    search_fields = ('review_number', 'worker__username', 'worker__first_name')


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = (
        'payroll_number', 'worker', 'period_start', 'period_end',
        'regular_hours', 'overtime_hours', 'status', 'currency',
        'tenant', 'created_at',
    )
    list_filter = ('status', 'currency', 'tenant')
    search_fields = ('payroll_number', 'worker__username', 'worker__first_name')
