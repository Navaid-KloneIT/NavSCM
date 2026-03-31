from django.urls import path

from . import views

app_name = 'labor'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Labor Planning
    # -------------------------------------------------------------------------
    path('plans/', views.plan_list_view, name='plan_list'),
    path('plans/add/', views.plan_create_view, name='plan_create'),
    path('plans/<int:pk>/', views.plan_detail_view, name='plan_detail'),
    path('plans/<int:pk>/edit/', views.plan_edit_view, name='plan_edit'),
    path('plans/<int:pk>/delete/', views.plan_delete_view, name='plan_delete'),
    path('plans/<int:pk>/approve/', views.plan_approve_view, name='plan_approve'),
    path('plans/<int:pk>/activate/', views.plan_activate_view, name='plan_activate'),
    path('plans/<int:pk>/complete/', views.plan_complete_view, name='plan_complete'),
    path('plans/<int:pk>/cancel/', views.plan_cancel_view, name='plan_cancel'),

    # -------------------------------------------------------------------------
    # Time & Attendance
    # -------------------------------------------------------------------------
    path('attendance/', views.attendance_list_view, name='attendance_list'),
    path('attendance/add/', views.attendance_create_view, name='attendance_create'),
    path('attendance/<int:pk>/', views.attendance_detail_view, name='attendance_detail'),
    path('attendance/<int:pk>/edit/', views.attendance_edit_view, name='attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete_view, name='attendance_delete'),
    path('attendance/<int:pk>/clock-out/', views.attendance_clock_out_view, name='attendance_clock_out'),
    path('attendance/<int:pk>/approve/', views.attendance_approve_view, name='attendance_approve'),
    path('attendance/<int:pk>/lock/', views.attendance_lock_view, name='attendance_lock'),

    # -------------------------------------------------------------------------
    # Task Assignment
    # -------------------------------------------------------------------------
    path('tasks/', views.task_list_view, name='task_list'),
    path('tasks/add/', views.task_create_view, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit_view, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete_view, name='task_delete'),
    path('tasks/<int:pk>/assign/', views.task_assign_view, name='task_assign'),
    path('tasks/<int:pk>/start/', views.task_start_view, name='task_start'),
    path('tasks/<int:pk>/complete/', views.task_complete_view, name='task_complete'),
    path('tasks/<int:pk>/cancel/', views.task_cancel_view, name='task_cancel'),

    # -------------------------------------------------------------------------
    # Performance Tracking
    # -------------------------------------------------------------------------
    path('performance/', views.performance_list_view, name='performance_list'),
    path('performance/add/', views.performance_create_view, name='performance_create'),
    path('performance/<int:pk>/', views.performance_detail_view, name='performance_detail'),
    path('performance/<int:pk>/edit/', views.performance_edit_view, name='performance_edit'),
    path('performance/<int:pk>/delete/', views.performance_delete_view, name='performance_delete'),
    path('performance/<int:pk>/submit/', views.performance_submit_view, name='performance_submit'),
    path('performance/<int:pk>/approve/', views.performance_approve_view, name='performance_approve'),
    path('performance/<int:pk>/close/', views.performance_close_view, name='performance_close'),
    path('performance/<int:pk>/cancel/', views.performance_cancel_view, name='performance_cancel'),

    # -------------------------------------------------------------------------
    # Payroll Integration
    # -------------------------------------------------------------------------
    path('payroll/', views.payroll_list_view, name='payroll_list'),
    path('payroll/add/', views.payroll_create_view, name='payroll_create'),
    path('payroll/<int:pk>/', views.payroll_detail_view, name='payroll_detail'),
    path('payroll/<int:pk>/edit/', views.payroll_edit_view, name='payroll_edit'),
    path('payroll/<int:pk>/delete/', views.payroll_delete_view, name='payroll_delete'),
    path('payroll/<int:pk>/calculate/', views.payroll_calculate_view, name='payroll_calculate'),
    path('payroll/<int:pk>/approve/', views.payroll_approve_view, name='payroll_approve'),
    path('payroll/<int:pk>/export/', views.payroll_export_view, name='payroll_export'),
    path('payroll/<int:pk>/cancel/', views.payroll_cancel_view, name='payroll_cancel'),
]
