from django.urls import path

from . import views

app_name = 'procurement'

urlpatterns = [
    # Item Categories
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    # Items
    path('items/', views.item_list_view, name='item_list'),
    path('items/add/', views.item_create_view, name='item_create'),
    path('items/<int:pk>/edit/', views.item_edit_view, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete_view, name='item_delete'),

    # Vendors
    path('vendors/', views.vendor_list_view, name='vendor_list'),
    path('vendors/add/', views.vendor_create_view, name='vendor_create'),
    path('vendors/<int:pk>/', views.vendor_detail_view, name='vendor_detail'),
    path('vendors/<int:pk>/edit/', views.vendor_edit_view, name='vendor_edit'),
    path('vendors/<int:pk>/delete/', views.vendor_delete_view, name='vendor_delete'),

    # Purchase Requisitions
    path('requisitions/', views.requisition_list_view, name='requisition_list'),
    path('requisitions/add/', views.requisition_create_view, name='requisition_create'),
    path('requisitions/<int:pk>/', views.requisition_detail_view, name='requisition_detail'),
    path('requisitions/<int:pk>/edit/', views.requisition_edit_view, name='requisition_edit'),
    path('requisitions/<int:pk>/submit/', views.requisition_submit_view, name='requisition_submit'),
    path('requisitions/<int:pk>/approve/', views.requisition_approve_view, name='requisition_approve'),
    path('requisitions/<int:pk>/delete/', views.requisition_delete_view, name='requisition_delete'),

    # RFQs
    path('rfqs/', views.rfq_list_view, name='rfq_list'),
    path('rfqs/add/', views.rfq_create_view, name='rfq_create'),
    path('rfqs/<int:pk>/', views.rfq_detail_view, name='rfq_detail'),
    path('rfqs/<int:pk>/edit/', views.rfq_edit_view, name='rfq_edit'),
    path('rfqs/<int:pk>/delete/', views.rfq_delete_view, name='rfq_delete'),

    # Purchase Orders
    path('purchase-orders/', views.po_list_view, name='po_list'),
    path('purchase-orders/add/', views.po_create_view, name='po_create'),
    path('purchase-orders/<int:pk>/', views.po_detail_view, name='po_detail'),
    path('purchase-orders/<int:pk>/edit/', views.po_edit_view, name='po_edit'),
    path('purchase-orders/<int:pk>/submit/', views.po_submit_view, name='po_submit'),
    path('purchase-orders/<int:pk>/approve/', views.po_approve_view, name='po_approve'),
    path('purchase-orders/<int:pk>/cancel/', views.po_cancel_view, name='po_cancel'),
    path('purchase-orders/<int:pk>/delete/', views.po_delete_view, name='po_delete'),

    # Goods Receipt Notes
    path('grns/', views.grn_list_view, name='grn_list'),
    path('grns/add/', views.grn_create_view, name='grn_create'),
    path('grns/<int:pk>/', views.grn_detail_view, name='grn_detail'),
    path('grns/<int:pk>/delete/', views.grn_delete_view, name='grn_delete'),

    # Vendor Invoices
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/add/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:pk>/delete/', views.invoice_delete_view, name='invoice_delete'),

    # Reconciliation (3-Way Match)
    path('reconciliation/', views.reconciliation_view, name='reconciliation'),
    path('reconciliation/add/', views.reconciliation_create_view, name='reconciliation_create'),
]
