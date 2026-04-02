from django.urls import path

from . import views

app_name = 'tpl'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Clients
    # -------------------------------------------------------------------------
    path('clients/', views.client_list_view, name='client_list'),
    path('clients/add/', views.client_create_view, name='client_create'),
    path('clients/<int:pk>/', views.client_detail_view, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_edit_view, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete_view, name='client_delete'),
    path('clients/<int:pk>/activate/', views.client_activate_view, name='client_activate'),
    path('clients/<int:pk>/suspend/', views.client_suspend_view, name='client_suspend'),
    path('clients/<int:pk>/terminate/', views.client_terminate_view, name='client_terminate'),

    # -------------------------------------------------------------------------
    # Billing Rates
    # -------------------------------------------------------------------------
    path('billing-rates/', views.billing_rate_list_view, name='billing_rate_list'),
    path('billing-rates/add/', views.billing_rate_create_view, name='billing_rate_create'),
    path('billing-rates/<int:pk>/', views.billing_rate_detail_view, name='billing_rate_detail'),
    path('billing-rates/<int:pk>/edit/', views.billing_rate_edit_view, name='billing_rate_edit'),
    path('billing-rates/<int:pk>/delete/', views.billing_rate_delete_view, name='billing_rate_delete'),

    # -------------------------------------------------------------------------
    # Billing Invoices
    # -------------------------------------------------------------------------
    path('invoices/', views.billing_invoice_list_view, name='billing_invoice_list'),
    path('invoices/add/', views.billing_invoice_create_view, name='billing_invoice_create'),
    path('invoices/<int:pk>/', views.billing_invoice_detail_view, name='billing_invoice_detail'),
    path('invoices/<int:pk>/edit/', views.billing_invoice_edit_view, name='billing_invoice_edit'),
    path('invoices/<int:pk>/delete/', views.billing_invoice_delete_view, name='billing_invoice_delete'),
    path('invoices/<int:pk>/send/', views.billing_invoice_send_view, name='billing_invoice_send'),
    path('invoices/<int:pk>/paid/', views.billing_invoice_paid_view, name='billing_invoice_paid'),
    path('invoices/<int:pk>/overdue/', views.billing_invoice_overdue_view, name='billing_invoice_overdue'),
    path('invoices/<int:pk>/cancel/', views.billing_invoice_cancel_view, name='billing_invoice_cancel'),

    # -------------------------------------------------------------------------
    # Client Storage Zones
    # -------------------------------------------------------------------------
    path('storage-zones/', views.storage_zone_list_view, name='storage_zone_list'),
    path('storage-zones/add/', views.storage_zone_create_view, name='storage_zone_create'),
    path('storage-zones/<int:pk>/', views.storage_zone_detail_view, name='storage_zone_detail'),
    path('storage-zones/<int:pk>/edit/', views.storage_zone_edit_view, name='storage_zone_edit'),
    path('storage-zones/<int:pk>/delete/', views.storage_zone_delete_view, name='storage_zone_delete'),

    # -------------------------------------------------------------------------
    # Client Inventory
    # -------------------------------------------------------------------------
    path('client-inventory/', views.client_inventory_list_view, name='client_inventory_list'),
    path('client-inventory/add/', views.client_inventory_create_view, name='client_inventory_create'),
    path('client-inventory/<int:pk>/', views.client_inventory_detail_view, name='client_inventory_detail'),
    path('client-inventory/<int:pk>/edit/', views.client_inventory_edit_view, name='client_inventory_edit'),
    path('client-inventory/<int:pk>/delete/', views.client_inventory_delete_view, name='client_inventory_delete'),

    # -------------------------------------------------------------------------
    # SLAs
    # -------------------------------------------------------------------------
    path('slas/', views.sla_list_view, name='sla_list'),
    path('slas/add/', views.sla_create_view, name='sla_create'),
    path('slas/<int:pk>/', views.sla_detail_view, name='sla_detail'),
    path('slas/<int:pk>/edit/', views.sla_edit_view, name='sla_edit'),
    path('slas/<int:pk>/delete/', views.sla_delete_view, name='sla_delete'),
    path('slas/<int:pk>/activate/', views.sla_activate_view, name='sla_activate'),
    path('slas/<int:pk>/breached/', views.sla_breached_view, name='sla_breached'),
    path('slas/<int:pk>/expire/', views.sla_expire_view, name='sla_expire'),

    # -------------------------------------------------------------------------
    # Client Integrations
    # -------------------------------------------------------------------------
    path('integrations/', views.integration_list_view, name='integration_list'),
    path('integrations/add/', views.integration_create_view, name='integration_create'),
    path('integrations/<int:pk>/', views.integration_detail_view, name='integration_detail'),
    path('integrations/<int:pk>/edit/', views.integration_edit_view, name='integration_edit'),
    path('integrations/<int:pk>/delete/', views.integration_delete_view, name='integration_delete'),
    path('integrations/<int:pk>/activate/', views.integration_activate_view, name='integration_activate'),
    path('integrations/<int:pk>/pause/', views.integration_pause_view, name='integration_pause'),
    path('integrations/<int:pk>/disable/', views.integration_disable_view, name='integration_disable'),

    # -------------------------------------------------------------------------
    # Rental Agreements
    # -------------------------------------------------------------------------
    path('rentals/', views.rental_list_view, name='rental_list'),
    path('rentals/add/', views.rental_create_view, name='rental_create'),
    path('rentals/<int:pk>/', views.rental_detail_view, name='rental_detail'),
    path('rentals/<int:pk>/edit/', views.rental_edit_view, name='rental_edit'),
    path('rentals/<int:pk>/delete/', views.rental_delete_view, name='rental_delete'),
    path('rentals/<int:pk>/activate/', views.rental_activate_view, name='rental_activate'),
    path('rentals/<int:pk>/expire/', views.rental_expire_view, name='rental_expire'),
    path('rentals/<int:pk>/terminate/', views.rental_terminate_view, name='rental_terminate'),
]
