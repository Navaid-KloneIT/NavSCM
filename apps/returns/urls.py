from django.urls import path

from . import views

app_name = 'returns'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Return Authorizations (RMA)
    # -------------------------------------------------------------------------
    path('rma/', views.rma_list_view, name='rma_list'),
    path('rma/add/', views.rma_create_view, name='rma_create'),
    path('rma/<int:pk>/', views.rma_detail_view, name='rma_detail'),
    path('rma/<int:pk>/edit/', views.rma_edit_view, name='rma_edit'),
    path('rma/<int:pk>/delete/', views.rma_delete_view, name='rma_delete'),
    path('rma/<int:pk>/submit/', views.rma_submit_view, name='rma_submit'),
    path('rma/<int:pk>/approve/', views.rma_approve_view, name='rma_approve'),
    path('rma/<int:pk>/reject/', views.rma_reject_view, name='rma_reject'),
    path('rma/<int:pk>/receive/', views.rma_receive_view, name='rma_receive'),
    path('rma/<int:pk>/received/', views.rma_received_view, name='rma_received'),
    path('rma/<int:pk>/close/', views.rma_close_view, name='rma_close'),

    # -------------------------------------------------------------------------
    # Refunds
    # -------------------------------------------------------------------------
    path('refunds/', views.refund_list_view, name='refund_list'),
    path('refunds/add/', views.refund_create_view, name='refund_create'),
    path('refunds/<int:pk>/', views.refund_detail_view, name='refund_detail'),
    path('refunds/<int:pk>/edit/', views.refund_edit_view, name='refund_edit'),
    path('refunds/<int:pk>/delete/', views.refund_delete_view, name='refund_delete'),
    path('refunds/<int:pk>/submit/', views.refund_submit_view, name='refund_submit'),
    path('refunds/<int:pk>/approve/', views.refund_approve_view, name='refund_approve'),
    path('refunds/<int:pk>/process/', views.refund_process_view, name='refund_process'),
    path('refunds/<int:pk>/complete/', views.refund_complete_view, name='refund_complete'),

    # -------------------------------------------------------------------------
    # Dispositions
    # -------------------------------------------------------------------------
    path('dispositions/', views.disposition_list_view, name='disposition_list'),
    path('dispositions/add/', views.disposition_create_view, name='disposition_create'),
    path('dispositions/<int:pk>/', views.disposition_detail_view, name='disposition_detail'),
    path('dispositions/<int:pk>/edit/', views.disposition_edit_view, name='disposition_edit'),
    path('dispositions/<int:pk>/delete/', views.disposition_delete_view, name='disposition_delete'),
    path('dispositions/<int:pk>/inspect/', views.disposition_inspect_view, name='disposition_inspect'),
    path('dispositions/<int:pk>/decide/', views.disposition_decide_view, name='disposition_decide'),
    path('dispositions/<int:pk>/process/', views.disposition_process_view, name='disposition_process'),
    path('dispositions/<int:pk>/complete/', views.disposition_complete_view, name='disposition_complete'),

    # -------------------------------------------------------------------------
    # Warranty Claims
    # -------------------------------------------------------------------------
    path('warranties/', views.warranty_list_view, name='warranty_list'),
    path('warranties/add/', views.warranty_create_view, name='warranty_create'),
    path('warranties/<int:pk>/', views.warranty_detail_view, name='warranty_detail'),
    path('warranties/<int:pk>/edit/', views.warranty_edit_view, name='warranty_edit'),
    path('warranties/<int:pk>/delete/', views.warranty_delete_view, name='warranty_delete'),
    path('warranties/<int:pk>/submit/', views.warranty_submit_view, name='warranty_submit'),
    path('warranties/<int:pk>/review/', views.warranty_review_view, name='warranty_review'),
    path('warranties/<int:pk>/approve/', views.warranty_approve_view, name='warranty_approve'),
    path('warranties/<int:pk>/settle/', views.warranty_settle_view, name='warranty_settle'),
    path('warranties/<int:pk>/deny/', views.warranty_deny_view, name='warranty_deny'),
    path('warranties/<int:pk>/close/', views.warranty_close_view, name='warranty_close'),

    # -------------------------------------------------------------------------
    # Return Portal Settings
    # -------------------------------------------------------------------------
    path('settings/', views.portal_settings_view, name='portal_settings'),
]
