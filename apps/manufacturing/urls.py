from django.urls import path

from . import views

app_name = 'manufacturing'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Work Centers
    # -------------------------------------------------------------------------
    path('work-centers/', views.workcenter_list_view, name='workcenter_list'),
    path('work-centers/add/', views.workcenter_create_view, name='workcenter_create'),
    path('work-centers/<int:pk>/', views.workcenter_detail_view, name='workcenter_detail'),
    path('work-centers/<int:pk>/edit/', views.workcenter_edit_view, name='workcenter_edit'),
    path('work-centers/<int:pk>/delete/', views.workcenter_delete_view, name='workcenter_delete'),

    # -------------------------------------------------------------------------
    # Bill of Materials
    # -------------------------------------------------------------------------
    path('boms/', views.bom_list_view, name='bom_list'),
    path('boms/add/', views.bom_create_view, name='bom_create'),
    path('boms/<int:pk>/', views.bom_detail_view, name='bom_detail'),
    path('boms/<int:pk>/edit/', views.bom_edit_view, name='bom_edit'),
    path('boms/<int:pk>/activate/', views.bom_activate_view, name='bom_activate'),
    path('boms/<int:pk>/obsolete/', views.bom_obsolete_view, name='bom_obsolete'),
    path('boms/<int:pk>/delete/', views.bom_delete_view, name='bom_delete'),

    # -------------------------------------------------------------------------
    # Production Schedules
    # -------------------------------------------------------------------------
    path('schedules/', views.schedule_list_view, name='schedule_list'),
    path('schedules/add/', views.schedule_create_view, name='schedule_create'),
    path('schedules/<int:pk>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedules/<int:pk>/edit/', views.schedule_edit_view, name='schedule_edit'),
    path('schedules/<int:pk>/plan/', views.schedule_plan_view, name='schedule_plan'),
    path('schedules/<int:pk>/start/', views.schedule_start_view, name='schedule_start'),
    path('schedules/<int:pk>/complete/', views.schedule_complete_view, name='schedule_complete'),
    path('schedules/<int:pk>/cancel/', views.schedule_cancel_view, name='schedule_cancel'),
    path('schedules/<int:pk>/delete/', views.schedule_delete_view, name='schedule_delete'),

    # -------------------------------------------------------------------------
    # Work Orders
    # -------------------------------------------------------------------------
    path('work-orders/', views.workorder_list_view, name='workorder_list'),
    path('work-orders/add/', views.workorder_create_view, name='workorder_create'),
    path('work-orders/<int:pk>/', views.workorder_detail_view, name='workorder_detail'),
    path('work-orders/<int:pk>/edit/', views.workorder_edit_view, name='workorder_edit'),
    path('work-orders/<int:pk>/release/', views.workorder_release_view, name='workorder_release'),
    path('work-orders/<int:pk>/start/', views.workorder_start_view, name='workorder_start'),
    path('work-orders/<int:pk>/hold/', views.workorder_hold_view, name='workorder_hold'),
    path('work-orders/<int:pk>/resume/', views.workorder_resume_view, name='workorder_resume'),
    path('work-orders/<int:pk>/complete/', views.workorder_complete_view, name='workorder_complete'),
    path('work-orders/<int:pk>/cancel/', views.workorder_cancel_view, name='workorder_cancel'),
    path('work-orders/<int:pk>/delete/', views.workorder_delete_view, name='workorder_delete'),

    # -------------------------------------------------------------------------
    # MRP
    # -------------------------------------------------------------------------
    path('mrp/', views.mrp_list_view, name='mrp_list'),
    path('mrp/add/', views.mrp_create_view, name='mrp_create'),
    path('mrp/<int:pk>/', views.mrp_detail_view, name='mrp_detail'),
    path('mrp/<int:pk>/run/', views.mrp_run_view, name='mrp_run'),
    path('mrp/<int:pk>/delete/', views.mrp_delete_view, name='mrp_delete'),

    # -------------------------------------------------------------------------
    # Production Logs (Shop Floor)
    # -------------------------------------------------------------------------
    path('logs/', views.log_list_view, name='log_list'),
    path('logs/add/', views.log_create_view, name='log_create'),
    path('logs/<int:pk>/', views.log_detail_view, name='log_detail'),
    path('logs/<int:pk>/edit/', views.log_edit_view, name='log_edit'),
    path('logs/<int:pk>/delete/', views.log_delete_view, name='log_delete'),
]
