from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('tenants/', views.tenant_list_view, name='tenant_list'),
    path('tenants/add/', views.tenant_add_view, name='tenant_add'),
    path('subscriptions/plans/', views.subscription_plans_view, name='subscription_plans'),
    path('subscriptions/billing/', views.subscription_billing_view, name='subscription_billing'),
    path('audit-logs/', views.audit_log_view, name='audit_logs'),
    path('security/', views.security_view, name='security'),
]
