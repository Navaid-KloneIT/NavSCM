from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('tenants/', views.tenant_list_view, name='tenant_list'),
    path('tenants/<uuid:pk>/', views.tenant_detail_view, name='tenant_detail'),
    path('tenants/add/', views.tenant_add_view, name='tenant_add'),
    path('subscriptions/plans/', views.subscription_plans_view, name='subscription_plans'),
    path('subscriptions/billing/', views.subscription_billing_view, name='subscription_billing'),
    path('subscriptions/billing/invoice/<str:invoice_number>/download/', views.invoice_download_view, name='invoice_download'),
    path('audit-logs/', views.audit_log_view, name='audit_logs'),
    path('security/', views.security_view, name='security'),
]
