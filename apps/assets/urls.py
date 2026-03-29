from django.urls import path

from . import views

app_name = 'assets'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Asset Registry
    # -------------------------------------------------------------------------
    path('registry/', views.asset_list_view, name='asset_list'),
    path('registry/add/', views.asset_create_view, name='asset_create'),
    path('registry/<int:pk>/', views.asset_detail_view, name='asset_detail'),
    path('registry/<int:pk>/edit/', views.asset_edit_view, name='asset_edit'),
    path('registry/<int:pk>/delete/', views.asset_delete_view, name='asset_delete'),
    path('registry/<int:pk>/activate/', views.asset_activate_view, name='asset_activate'),
    path('registry/<int:pk>/maintenance/', views.asset_maintenance_view, name='asset_maintenance'),
    path('registry/<int:pk>/restore/', views.asset_restore_view, name='asset_restore'),
    path('registry/<int:pk>/retire/', views.asset_retire_view, name='asset_retire'),

    # -------------------------------------------------------------------------
    # Preventive Maintenance
    # -------------------------------------------------------------------------
    path('preventive/', views.pm_list_view, name='pm_list'),
    path('preventive/add/', views.pm_create_view, name='pm_create'),
    path('preventive/<int:pk>/', views.pm_detail_view, name='pm_detail'),
    path('preventive/<int:pk>/edit/', views.pm_edit_view, name='pm_edit'),
    path('preventive/<int:pk>/delete/', views.pm_delete_view, name='pm_delete'),
    path('preventive/<int:pk>/schedule/', views.pm_schedule_view, name='pm_schedule'),
    path('preventive/<int:pk>/start/', views.pm_start_view, name='pm_start'),
    path('preventive/<int:pk>/complete/', views.pm_complete_view, name='pm_complete'),
    path('preventive/<int:pk>/cancel/', views.pm_cancel_view, name='pm_cancel'),

    # -------------------------------------------------------------------------
    # Breakdown Maintenance
    # -------------------------------------------------------------------------
    path('breakdowns/', views.bm_list_view, name='bm_list'),
    path('breakdowns/add/', views.bm_create_view, name='bm_create'),
    path('breakdowns/<int:pk>/', views.bm_detail_view, name='bm_detail'),
    path('breakdowns/<int:pk>/edit/', views.bm_edit_view, name='bm_edit'),
    path('breakdowns/<int:pk>/delete/', views.bm_delete_view, name='bm_delete'),
    path('breakdowns/<int:pk>/assign/', views.bm_assign_view, name='bm_assign'),
    path('breakdowns/<int:pk>/diagnose/', views.bm_diagnose_view, name='bm_diagnose'),
    path('breakdowns/<int:pk>/repair/', views.bm_repair_view, name='bm_repair'),
    path('breakdowns/<int:pk>/complete/', views.bm_complete_view, name='bm_complete'),
    path('breakdowns/<int:pk>/close/', views.bm_close_view, name='bm_close'),

    # -------------------------------------------------------------------------
    # Spare Parts Inventory
    # -------------------------------------------------------------------------
    path('spare-parts/', views.spare_list_view, name='spare_list'),
    path('spare-parts/add/', views.spare_create_view, name='spare_create'),
    path('spare-parts/<int:pk>/', views.spare_detail_view, name='spare_detail'),
    path('spare-parts/<int:pk>/edit/', views.spare_edit_view, name='spare_edit'),
    path('spare-parts/<int:pk>/delete/', views.spare_delete_view, name='spare_delete'),

    # -------------------------------------------------------------------------
    # Asset Depreciation
    # -------------------------------------------------------------------------
    path('depreciation/', views.depreciation_list_view, name='depreciation_list'),
    path('depreciation/add/', views.depreciation_create_view, name='depreciation_create'),
    path('depreciation/<int:pk>/', views.depreciation_detail_view, name='depreciation_detail'),
    path('depreciation/<int:pk>/edit/', views.depreciation_edit_view, name='depreciation_edit'),
    path('depreciation/<int:pk>/delete/', views.depreciation_delete_view, name='depreciation_delete'),
    path('depreciation/<int:pk>/activate/', views.depreciation_activate_view, name='depreciation_activate'),
    path('depreciation/<int:pk>/fully-depreciated/', views.depreciation_fully_depreciated_view, name='depreciation_fully_depreciated'),
    path('depreciation/<int:pk>/dispose/', views.depreciation_dispose_view, name='depreciation_dispose'),
]
