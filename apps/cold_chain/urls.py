from django.urls import path

from . import views

app_name = 'cold_chain'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Temperature Sensors
    # -------------------------------------------------------------------------
    path('sensors/', views.sensor_list_view, name='sensor_list'),
    path('sensors/add/', views.sensor_create_view, name='sensor_create'),
    path('sensors/<int:pk>/', views.sensor_detail_view, name='sensor_detail'),
    path('sensors/<int:pk>/edit/', views.sensor_edit_view, name='sensor_edit'),
    path('sensors/<int:pk>/delete/', views.sensor_delete_view, name='sensor_delete'),
    path('sensors/<int:pk>/activate/', views.sensor_activate_view, name='sensor_activate'),
    path('sensors/<int:pk>/offline/', views.sensor_offline_view, name='sensor_offline'),
    path('sensors/<int:pk>/maintenance/', views.sensor_maintenance_view, name='sensor_maintenance'),
    path('sensors/<int:pk>/retire/', views.sensor_retire_view, name='sensor_retire'),

    # -------------------------------------------------------------------------
    # Temperature Zones
    # -------------------------------------------------------------------------
    path('zones/', views.zone_list_view, name='zone_list'),
    path('zones/add/', views.zone_create_view, name='zone_create'),
    path('zones/<int:pk>/', views.zone_detail_view, name='zone_detail'),
    path('zones/<int:pk>/edit/', views.zone_edit_view, name='zone_edit'),
    path('zones/<int:pk>/delete/', views.zone_delete_view, name='zone_delete'),
    path('zones/<int:pk>/activate/', views.zone_activate_view, name='zone_activate'),
    path('zones/<int:pk>/deactivate/', views.zone_deactivate_view, name='zone_deactivate'),

    # -------------------------------------------------------------------------
    # Temperature Excursions
    # -------------------------------------------------------------------------
    path('excursions/', views.excursion_list_view, name='excursion_list'),
    path('excursions/add/', views.excursion_create_view, name='excursion_create'),
    path('excursions/<int:pk>/', views.excursion_detail_view, name='excursion_detail'),
    path('excursions/<int:pk>/edit/', views.excursion_edit_view, name='excursion_edit'),
    path('excursions/<int:pk>/delete/', views.excursion_delete_view, name='excursion_delete'),
    path('excursions/<int:pk>/acknowledge/', views.excursion_acknowledge_view, name='excursion_acknowledge'),
    path('excursions/<int:pk>/investigate/', views.excursion_investigate_view, name='excursion_investigate'),
    path('excursions/<int:pk>/resolve/', views.excursion_resolve_view, name='excursion_resolve'),
    path('excursions/<int:pk>/close/', views.excursion_close_view, name='excursion_close'),

    # -------------------------------------------------------------------------
    # Cold Storage Units
    # -------------------------------------------------------------------------
    path('storage/', views.storage_list_view, name='storage_list'),
    path('storage/add/', views.storage_create_view, name='storage_create'),
    path('storage/<int:pk>/', views.storage_detail_view, name='storage_detail'),
    path('storage/<int:pk>/edit/', views.storage_edit_view, name='storage_edit'),
    path('storage/<int:pk>/delete/', views.storage_delete_view, name='storage_delete'),
    path('storage/<int:pk>/activate/', views.storage_activate_view, name='storage_activate'),
    path('storage/<int:pk>/maintenance/', views.storage_maintenance_view, name='storage_maintenance'),
    path('storage/<int:pk>/restore/', views.storage_restore_view, name='storage_restore'),
    path('storage/<int:pk>/retire/', views.storage_retire_view, name='storage_retire'),

    # -------------------------------------------------------------------------
    # Compliance Reports
    # -------------------------------------------------------------------------
    path('compliance/', views.compliance_list_view, name='compliance_list'),
    path('compliance/add/', views.compliance_create_view, name='compliance_create'),
    path('compliance/<int:pk>/', views.compliance_detail_view, name='compliance_detail'),
    path('compliance/<int:pk>/edit/', views.compliance_edit_view, name='compliance_edit'),
    path('compliance/<int:pk>/delete/', views.compliance_delete_view, name='compliance_delete'),
    path('compliance/<int:pk>/generate/', views.compliance_generate_view, name='compliance_generate'),
    path('compliance/<int:pk>/review/', views.compliance_review_view, name='compliance_review'),
    path('compliance/<int:pk>/submit/', views.compliance_submit_view, name='compliance_submit'),
    path('compliance/<int:pk>/approve/', views.compliance_approve_view, name='compliance_approve'),

    # -------------------------------------------------------------------------
    # Reefer Units
    # -------------------------------------------------------------------------
    path('reefers/', views.reefer_list_view, name='reefer_list'),
    path('reefers/add/', views.reefer_create_view, name='reefer_create'),
    path('reefers/<int:pk>/', views.reefer_detail_view, name='reefer_detail'),
    path('reefers/<int:pk>/edit/', views.reefer_edit_view, name='reefer_edit'),
    path('reefers/<int:pk>/delete/', views.reefer_delete_view, name='reefer_delete'),
    path('reefers/<int:pk>/activate/', views.reefer_activate_view, name='reefer_activate'),
    path('reefers/<int:pk>/maintenance/', views.reefer_maintenance_status_view, name='reefer_maintenance_status'),
    path('reefers/<int:pk>/restore/', views.reefer_restore_view, name='reefer_restore'),
    path('reefers/<int:pk>/retire/', views.reefer_retire_view, name='reefer_retire'),

    # -------------------------------------------------------------------------
    # Reefer Maintenance
    # -------------------------------------------------------------------------
    path('reefer-maintenance/', views.reefer_maint_list_view, name='reefer_maint_list'),
    path('reefer-maintenance/add/', views.reefer_maint_create_view, name='reefer_maint_create'),
    path('reefer-maintenance/<int:pk>/', views.reefer_maint_detail_view, name='reefer_maint_detail'),
    path('reefer-maintenance/<int:pk>/edit/', views.reefer_maint_edit_view, name='reefer_maint_edit'),
    path('reefer-maintenance/<int:pk>/delete/', views.reefer_maint_delete_view, name='reefer_maint_delete'),
    path('reefer-maintenance/<int:pk>/schedule/', views.reefer_maint_schedule_view, name='reefer_maint_schedule'),
    path('reefer-maintenance/<int:pk>/start/', views.reefer_maint_start_view, name='reefer_maint_start'),
    path('reefer-maintenance/<int:pk>/complete/', views.reefer_maint_complete_view, name='reefer_maint_complete'),
    path('reefer-maintenance/<int:pk>/cancel/', views.reefer_maint_cancel_view, name='reefer_maint_cancel'),
]
