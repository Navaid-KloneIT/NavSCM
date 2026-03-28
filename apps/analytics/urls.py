from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------------------
    path('', views.dashboard_view, name='dashboard'),

    # -------------------------------------------------------------------------
    # Inventory Analytics
    # -------------------------------------------------------------------------
    path('inventory/', views.inventory_list_view, name='inventory_list'),
    path('inventory/add/', views.inventory_create_view, name='inventory_create'),
    path('inventory/<int:pk>/', views.inventory_detail_view, name='inventory_detail'),
    path('inventory/<int:pk>/edit/', views.inventory_edit_view, name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views.inventory_delete_view, name='inventory_delete'),
    path('inventory/<int:pk>/generate/', views.inventory_generate_view, name='inventory_generate'),
    path('inventory/<int:pk>/review/', views.inventory_review_view, name='inventory_review'),
    path('inventory/<int:pk>/archive/', views.inventory_archive_view, name='inventory_archive'),

    # -------------------------------------------------------------------------
    # Procurement Analytics
    # -------------------------------------------------------------------------
    path('procurement/', views.procurement_list_view, name='procurement_list'),
    path('procurement/add/', views.procurement_create_view, name='procurement_create'),
    path('procurement/<int:pk>/', views.procurement_detail_view, name='procurement_detail'),
    path('procurement/<int:pk>/edit/', views.procurement_edit_view, name='procurement_edit'),
    path('procurement/<int:pk>/delete/', views.procurement_delete_view, name='procurement_delete'),
    path('procurement/<int:pk>/generate/', views.procurement_generate_view, name='procurement_generate'),
    path('procurement/<int:pk>/review/', views.procurement_review_view, name='procurement_review'),
    path('procurement/<int:pk>/archive/', views.procurement_archive_view, name='procurement_archive'),

    # -------------------------------------------------------------------------
    # Logistics KPIs
    # -------------------------------------------------------------------------
    path('logistics/', views.logistics_list_view, name='logistics_list'),
    path('logistics/add/', views.logistics_create_view, name='logistics_create'),
    path('logistics/<int:pk>/', views.logistics_detail_view, name='logistics_detail'),
    path('logistics/<int:pk>/edit/', views.logistics_edit_view, name='logistics_edit'),
    path('logistics/<int:pk>/delete/', views.logistics_delete_view, name='logistics_delete'),
    path('logistics/<int:pk>/generate/', views.logistics_generate_view, name='logistics_generate'),
    path('logistics/<int:pk>/review/', views.logistics_review_view, name='logistics_review'),
    path('logistics/<int:pk>/archive/', views.logistics_archive_view, name='logistics_archive'),

    # -------------------------------------------------------------------------
    # Financial Reports
    # -------------------------------------------------------------------------
    path('financial/', views.financial_list_view, name='financial_list'),
    path('financial/add/', views.financial_create_view, name='financial_create'),
    path('financial/<int:pk>/', views.financial_detail_view, name='financial_detail'),
    path('financial/<int:pk>/edit/', views.financial_edit_view, name='financial_edit'),
    path('financial/<int:pk>/delete/', views.financial_delete_view, name='financial_delete'),
    path('financial/<int:pk>/generate/', views.financial_generate_view, name='financial_generate'),
    path('financial/<int:pk>/review/', views.financial_review_view, name='financial_review'),
    path('financial/<int:pk>/archive/', views.financial_archive_view, name='financial_archive'),

    # -------------------------------------------------------------------------
    # Predictive Alerts
    # -------------------------------------------------------------------------
    path('alerts/', views.alert_list_view, name='alert_list'),
    path('alerts/add/', views.alert_create_view, name='alert_create'),
    path('alerts/<int:pk>/', views.alert_detail_view, name='alert_detail'),
    path('alerts/<int:pk>/edit/', views.alert_edit_view, name='alert_edit'),
    path('alerts/<int:pk>/delete/', views.alert_delete_view, name='alert_delete'),
    path('alerts/<int:pk>/analyze/', views.alert_analyze_view, name='alert_analyze'),
    path('alerts/<int:pk>/confirm/', views.alert_confirm_view, name='alert_confirm'),
    path('alerts/<int:pk>/resolve/', views.alert_resolve_view, name='alert_resolve'),
    path('alerts/<int:pk>/dismiss/', views.alert_dismiss_view, name='alert_dismiss'),
]
