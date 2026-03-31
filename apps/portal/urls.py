from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Portal Accounts
    # -------------------------------------------------------------------------
    path('accounts/', views.account_list_view, name='account_list'),
    path('accounts/add/', views.account_create_view, name='account_create'),
    path('accounts/<int:pk>/', views.account_detail_view, name='account_detail'),
    path('accounts/<int:pk>/edit/', views.account_edit_view, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete_view, name='account_delete'),
    path('accounts/<int:pk>/activate/', views.account_activate_view, name='account_activate'),
    path('accounts/<int:pk>/suspend/', views.account_suspend_view, name='account_suspend'),
    path('accounts/<int:pk>/close/', views.account_close_view, name='account_close'),

    # -------------------------------------------------------------------------
    # Order Tracking
    # -------------------------------------------------------------------------
    path('tracking/', views.tracking_list_view, name='tracking_list'),
    path('tracking/add/', views.tracking_create_view, name='tracking_create'),
    path('tracking/<int:pk>/', views.tracking_detail_view, name='tracking_detail'),
    path('tracking/<int:pk>/edit/', views.tracking_edit_view, name='tracking_edit'),
    path('tracking/<int:pk>/delete/', views.tracking_delete_view, name='tracking_delete'),
    path('tracking/<int:pk>/ship/', views.tracking_ship_view, name='tracking_ship'),
    path('tracking/<int:pk>/deliver/', views.tracking_deliver_view, name='tracking_deliver'),
    path('tracking/<int:pk>/delay/', views.tracking_delay_view, name='tracking_delay'),
    path('tracking/<int:pk>/cancel/', views.tracking_cancel_view, name='tracking_cancel'),

    # -------------------------------------------------------------------------
    # Portal Documents
    # -------------------------------------------------------------------------
    path('documents/', views.document_list_view, name='document_list'),
    path('documents/add/', views.document_create_view, name='document_create'),
    path('documents/<int:pk>/', views.document_detail_view, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_edit_view, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete_view, name='document_delete'),
    path('documents/<int:pk>/publish/', views.document_publish_view, name='document_publish'),
    path('documents/<int:pk>/archive/', views.document_archive_view, name='document_archive'),

    # -------------------------------------------------------------------------
    # Support Tickets
    # -------------------------------------------------------------------------
    path('tickets/', views.ticket_list_view, name='ticket_list'),
    path('tickets/add/', views.ticket_create_view, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.ticket_edit_view, name='ticket_edit'),
    path('tickets/<int:pk>/delete/', views.ticket_delete_view, name='ticket_delete'),
    path('tickets/<int:pk>/assign/', views.ticket_assign_view, name='ticket_assign'),
    path('tickets/<int:pk>/progress/', views.ticket_progress_view, name='ticket_progress'),
    path('tickets/<int:pk>/resolve/', views.ticket_resolve_view, name='ticket_resolve'),
    path('tickets/<int:pk>/close/', views.ticket_close_view, name='ticket_close'),
    path('tickets/<int:pk>/reopen/', views.ticket_reopen_view, name='ticket_reopen'),

    # -------------------------------------------------------------------------
    # Catalog Browsing
    # -------------------------------------------------------------------------
    path('catalog/', views.catalog_list_view, name='catalog_list'),
    path('catalog/add/', views.catalog_create_view, name='catalog_create'),
    path('catalog/<int:pk>/', views.catalog_detail_view, name='catalog_detail'),
    path('catalog/<int:pk>/edit/', views.catalog_edit_view, name='catalog_edit'),
    path('catalog/<int:pk>/delete/', views.catalog_delete_view, name='catalog_delete'),
]
