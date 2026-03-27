from django.urls import path

from . import views

app_name = 'qms'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Inspection Templates
    # -------------------------------------------------------------------------
    path('templates/', views.template_list_view, name='template_list'),
    path('templates/add/', views.template_create_view, name='template_create'),
    path('templates/<int:pk>/', views.template_detail_view, name='template_detail'),
    path('templates/<int:pk>/edit/', views.template_edit_view, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete_view, name='template_delete'),

    # -------------------------------------------------------------------------
    # Quality Inspections
    # -------------------------------------------------------------------------
    path('inspections/', views.inspection_list_view, name='inspection_list'),
    path('inspections/add/', views.inspection_create_view, name='inspection_create'),
    path('inspections/<int:pk>/', views.inspection_detail_view, name='inspection_detail'),
    path('inspections/<int:pk>/edit/', views.inspection_edit_view, name='inspection_edit'),
    path('inspections/<int:pk>/start/', views.inspection_start_view, name='inspection_start'),
    path('inspections/<int:pk>/complete/', views.inspection_complete_view, name='inspection_complete'),
    path('inspections/<int:pk>/hold/', views.inspection_hold_view, name='inspection_hold'),
    path('inspections/<int:pk>/delete/', views.inspection_delete_view, name='inspection_delete'),

    # -------------------------------------------------------------------------
    # Non-Conformance Reports
    # -------------------------------------------------------------------------
    path('ncrs/', views.ncr_list_view, name='ncr_list'),
    path('ncrs/add/', views.ncr_create_view, name='ncr_create'),
    path('ncrs/<int:pk>/', views.ncr_detail_view, name='ncr_detail'),
    path('ncrs/<int:pk>/edit/', views.ncr_edit_view, name='ncr_edit'),
    path('ncrs/<int:pk>/open/', views.ncr_open_view, name='ncr_open'),
    path('ncrs/<int:pk>/investigate/', views.ncr_investigate_view, name='ncr_investigate'),
    path('ncrs/<int:pk>/resolve/', views.ncr_resolve_view, name='ncr_resolve'),
    path('ncrs/<int:pk>/close/', views.ncr_close_view, name='ncr_close'),
    path('ncrs/<int:pk>/delete/', views.ncr_delete_view, name='ncr_delete'),

    # -------------------------------------------------------------------------
    # CAPA
    # -------------------------------------------------------------------------
    path('capas/', views.capa_list_view, name='capa_list'),
    path('capas/add/', views.capa_create_view, name='capa_create'),
    path('capas/<int:pk>/', views.capa_detail_view, name='capa_detail'),
    path('capas/<int:pk>/edit/', views.capa_edit_view, name='capa_edit'),
    path('capas/<int:pk>/open/', views.capa_open_view, name='capa_open'),
    path('capas/<int:pk>/start/', views.capa_start_view, name='capa_start'),
    path('capas/<int:pk>/verify/', views.capa_verify_view, name='capa_verify'),
    path('capas/<int:pk>/complete/', views.capa_complete_view, name='capa_complete'),
    path('capas/<int:pk>/close/', views.capa_close_view, name='capa_close'),
    path('capas/<int:pk>/delete/', views.capa_delete_view, name='capa_delete'),

    # -------------------------------------------------------------------------
    # Quality Audits
    # -------------------------------------------------------------------------
    path('audits/', views.audit_list_view, name='audit_list'),
    path('audits/add/', views.audit_create_view, name='audit_create'),
    path('audits/<int:pk>/', views.audit_detail_view, name='audit_detail'),
    path('audits/<int:pk>/edit/', views.audit_edit_view, name='audit_edit'),
    path('audits/<int:pk>/schedule/', views.audit_schedule_view, name='audit_schedule'),
    path('audits/<int:pk>/start/', views.audit_start_view, name='audit_start'),
    path('audits/<int:pk>/complete/', views.audit_complete_view, name='audit_complete'),
    path('audits/<int:pk>/close/', views.audit_close_view, name='audit_close'),
    path('audits/<int:pk>/delete/', views.audit_delete_view, name='audit_delete'),

    # -------------------------------------------------------------------------
    # Certificates of Analysis
    # -------------------------------------------------------------------------
    path('coas/', views.coa_list_view, name='coa_list'),
    path('coas/add/', views.coa_create_view, name='coa_create'),
    path('coas/<int:pk>/', views.coa_detail_view, name='coa_detail'),
    path('coas/<int:pk>/edit/', views.coa_edit_view, name='coa_edit'),
    path('coas/<int:pk>/submit/', views.coa_submit_view, name='coa_submit'),
    path('coas/<int:pk>/approve/', views.coa_approve_view, name='coa_approve'),
    path('coas/<int:pk>/issue/', views.coa_issue_view, name='coa_issue'),
    path('coas/<int:pk>/revoke/', views.coa_revoke_view, name='coa_revoke'),
    path('coas/<int:pk>/delete/', views.coa_delete_view, name='coa_delete'),
]
