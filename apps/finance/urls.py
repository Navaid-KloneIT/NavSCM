from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    # -------------------------------------------------------------------------
    # AP Invoices
    # -------------------------------------------------------------------------
    path('ap-invoices/', views.ap_invoice_list_view, name='ap_invoice_list'),
    path('ap-invoices/add/', views.ap_invoice_create_view, name='ap_invoice_create'),
    path('ap-invoices/<int:pk>/', views.ap_invoice_detail_view, name='ap_invoice_detail'),
    path('ap-invoices/<int:pk>/edit/', views.ap_invoice_edit_view, name='ap_invoice_edit'),
    path('ap-invoices/<int:pk>/delete/', views.ap_invoice_delete_view, name='ap_invoice_delete'),
    path('ap-invoices/<int:pk>/approve/', views.ap_invoice_approve_view, name='ap_invoice_approve'),
    path('ap-invoices/<int:pk>/mark-overdue/', views.ap_invoice_overdue_view, name='ap_invoice_overdue'),
    path('ap-invoices/<int:pk>/cancel/', views.ap_invoice_cancel_view, name='ap_invoice_cancel'),

    # -------------------------------------------------------------------------
    # AP Payments
    # -------------------------------------------------------------------------
    path('ap-payments/', views.ap_payment_list_view, name='ap_payment_list'),
    path('ap-payments/add/', views.ap_payment_create_view, name='ap_payment_create'),
    path('ap-payments/<int:pk>/', views.ap_payment_detail_view, name='ap_payment_detail'),
    path('ap-payments/<int:pk>/delete/', views.ap_payment_delete_view, name='ap_payment_delete'),

    # -------------------------------------------------------------------------
    # AR Invoices
    # -------------------------------------------------------------------------
    path('ar-invoices/', views.ar_invoice_list_view, name='ar_invoice_list'),
    path('ar-invoices/add/', views.ar_invoice_create_view, name='ar_invoice_create'),
    path('ar-invoices/<int:pk>/', views.ar_invoice_detail_view, name='ar_invoice_detail'),
    path('ar-invoices/<int:pk>/edit/', views.ar_invoice_edit_view, name='ar_invoice_edit'),
    path('ar-invoices/<int:pk>/delete/', views.ar_invoice_delete_view, name='ar_invoice_delete'),
    path('ar-invoices/<int:pk>/send/', views.ar_invoice_send_view, name='ar_invoice_send'),
    path('ar-invoices/<int:pk>/mark-overdue/', views.ar_invoice_overdue_view, name='ar_invoice_overdue'),
    path('ar-invoices/<int:pk>/cancel/', views.ar_invoice_cancel_view, name='ar_invoice_cancel'),

    # -------------------------------------------------------------------------
    # AR Payments
    # -------------------------------------------------------------------------
    path('ar-payments/', views.ar_payment_list_view, name='ar_payment_list'),
    path('ar-payments/add/', views.ar_payment_create_view, name='ar_payment_create'),
    path('ar-payments/<int:pk>/', views.ar_payment_detail_view, name='ar_payment_detail'),
    path('ar-payments/<int:pk>/delete/', views.ar_payment_delete_view, name='ar_payment_delete'),

    # -------------------------------------------------------------------------
    # Landed Cost
    # -------------------------------------------------------------------------
    path('landed-costs/', views.landed_cost_list_view, name='landed_cost_list'),
    path('landed-costs/add/', views.landed_cost_create_view, name='landed_cost_create'),
    path('landed-costs/<int:pk>/', views.landed_cost_detail_view, name='landed_cost_detail'),
    path('landed-costs/<int:pk>/edit/', views.landed_cost_edit_view, name='landed_cost_edit'),
    path('landed-costs/<int:pk>/delete/', views.landed_cost_delete_view, name='landed_cost_delete'),
    path('landed-costs/<int:pk>/calculate/', views.landed_cost_calculate_view, name='landed_cost_calculate'),
    path('landed-costs/<int:pk>/finalize/', views.landed_cost_finalize_view, name='landed_cost_finalize'),

    # -------------------------------------------------------------------------
    # Budgets
    # -------------------------------------------------------------------------
    path('budgets/', views.budget_list_view, name='budget_list'),
    path('budgets/add/', views.budget_create_view, name='budget_create'),
    path('budgets/<int:pk>/', views.budget_detail_view, name='budget_detail'),
    path('budgets/<int:pk>/edit/', views.budget_edit_view, name='budget_edit'),
    path('budgets/<int:pk>/delete/', views.budget_delete_view, name='budget_delete'),
    path('budgets/<int:pk>/activate/', views.budget_activate_view, name='budget_activate'),
    path('budgets/<int:pk>/close/', views.budget_close_view, name='budget_close'),

    # -------------------------------------------------------------------------
    # Tax Rates
    # -------------------------------------------------------------------------
    path('tax-rates/', views.tax_rate_list_view, name='tax_rate_list'),
    path('tax-rates/add/', views.tax_rate_create_view, name='tax_rate_create'),
    path('tax-rates/<int:pk>/', views.tax_rate_detail_view, name='tax_rate_detail'),
    path('tax-rates/<int:pk>/edit/', views.tax_rate_edit_view, name='tax_rate_edit'),
    path('tax-rates/<int:pk>/delete/', views.tax_rate_delete_view, name='tax_rate_delete'),

    # -------------------------------------------------------------------------
    # Tax Transactions
    # -------------------------------------------------------------------------
    path('tax-transactions/', views.tax_transaction_list_view, name='tax_transaction_list'),
    path('tax-transactions/add/', views.tax_transaction_create_view, name='tax_transaction_create'),
    path('tax-transactions/<int:pk>/', views.tax_transaction_detail_view, name='tax_transaction_detail'),
]
