from django.urls import path

from . import views

app_name = 'contracts'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Contract Repository
    # -------------------------------------------------------------------------
    path('contracts/', views.contract_list_view, name='contract_list'),
    path('contracts/add/', views.contract_create_view, name='contract_create'),
    path('contracts/<int:pk>/', views.contract_detail_view, name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.contract_edit_view, name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.contract_delete_view, name='contract_delete'),
    path('contracts/<int:pk>/activate/', views.contract_activate_view, name='contract_activate'),
    path('contracts/<int:pk>/review/', views.contract_review_view, name='contract_review'),
    path('contracts/<int:pk>/terminate/', views.contract_terminate_view, name='contract_terminate'),
    path('contracts/<int:pk>/expire/', views.contract_expire_view, name='contract_expire'),

    # -------------------------------------------------------------------------
    # Compliance Tracking
    # -------------------------------------------------------------------------
    path('compliance/', views.compliance_list_view, name='compliance_list'),
    path('compliance/add/', views.compliance_create_view, name='compliance_create'),
    path('compliance/<int:pk>/', views.compliance_detail_view, name='compliance_detail'),
    path('compliance/<int:pk>/edit/', views.compliance_edit_view, name='compliance_edit'),
    path('compliance/<int:pk>/delete/', views.compliance_delete_view, name='compliance_delete'),
    path('compliance/<int:pk>/review/', views.compliance_review_view, name='compliance_review'),
    path('compliance/<int:pk>/compliant/', views.compliance_mark_compliant_view, name='compliance_compliant'),
    path('compliance/<int:pk>/non-compliant/', views.compliance_mark_non_compliant_view, name='compliance_non_compliant'),

    # -------------------------------------------------------------------------
    # Trade Documentation
    # -------------------------------------------------------------------------
    path('trade-docs/', views.trade_doc_list_view, name='trade_doc_list'),
    path('trade-docs/add/', views.trade_doc_create_view, name='trade_doc_create'),
    path('trade-docs/<int:pk>/', views.trade_doc_detail_view, name='trade_doc_detail'),
    path('trade-docs/<int:pk>/edit/', views.trade_doc_edit_view, name='trade_doc_edit'),
    path('trade-docs/<int:pk>/delete/', views.trade_doc_delete_view, name='trade_doc_delete'),
    path('trade-docs/<int:pk>/issue/', views.trade_doc_issue_view, name='trade_doc_issue'),
    path('trade-docs/<int:pk>/transit/', views.trade_doc_transit_view, name='trade_doc_transit'),
    path('trade-docs/<int:pk>/deliver/', views.trade_doc_deliver_view, name='trade_doc_deliver'),
    path('trade-docs/<int:pk>/archive/', views.trade_doc_archive_view, name='trade_doc_archive'),

    # -------------------------------------------------------------------------
    # License Management
    # -------------------------------------------------------------------------
    path('licenses/', views.license_list_view, name='license_list'),
    path('licenses/add/', views.license_create_view, name='license_create'),
    path('licenses/<int:pk>/', views.license_detail_view, name='license_detail'),
    path('licenses/<int:pk>/edit/', views.license_edit_view, name='license_edit'),
    path('licenses/<int:pk>/delete/', views.license_delete_view, name='license_delete'),
    path('licenses/<int:pk>/activate/', views.license_activate_view, name='license_activate'),
    path('licenses/<int:pk>/suspend/', views.license_suspend_view, name='license_suspend'),
    path('licenses/<int:pk>/revoke/', views.license_revoke_view, name='license_revoke'),
    path('licenses/<int:pk>/expire/', views.license_expire_view, name='license_expire'),

    # -------------------------------------------------------------------------
    # Sustainability Tracking
    # -------------------------------------------------------------------------
    path('sustainability/', views.sustainability_list_view, name='sustainability_list'),
    path('sustainability/add/', views.sustainability_create_view, name='sustainability_create'),
    path('sustainability/<int:pk>/', views.sustainability_detail_view, name='sustainability_detail'),
    path('sustainability/<int:pk>/edit/', views.sustainability_edit_view, name='sustainability_edit'),
    path('sustainability/<int:pk>/delete/', views.sustainability_delete_view, name='sustainability_delete'),
    path('sustainability/<int:pk>/submit/', views.sustainability_submit_view, name='sustainability_submit'),
    path('sustainability/<int:pk>/review/', views.sustainability_review_view, name='sustainability_review'),
    path('sustainability/<int:pk>/approve/', views.sustainability_approve_view, name='sustainability_approve'),
    path('sustainability/<int:pk>/publish/', views.sustainability_publish_view, name='sustainability_publish'),
]
