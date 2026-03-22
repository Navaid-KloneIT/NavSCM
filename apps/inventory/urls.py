from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Warehouses
    path('warehouses/', views.warehouse_list_view, name='warehouse_list'),
    path('warehouses/add/', views.warehouse_create_view, name='warehouse_create'),
    path('warehouses/<int:pk>/', views.warehouse_detail_view, name='warehouse_detail'),
    path('warehouses/<int:pk>/edit/', views.warehouse_edit_view, name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.warehouse_delete_view, name='warehouse_delete'),

    # Warehouse Locations
    path('warehouses/<int:warehouse_pk>/locations/add/', views.location_create_view, name='location_create'),
    path('locations/<int:pk>/edit/', views.location_edit_view, name='location_edit'),
    path('locations/<int:pk>/delete/', views.location_delete_view, name='location_delete'),

    # Stock Items
    path('stock/', views.stock_list_view, name='stock_list'),
    path('stock/<int:pk>/', views.stock_detail_view, name='stock_detail'),

    # Warehouse Transfers
    path('transfers/', views.transfer_list_view, name='transfer_list'),
    path('transfers/add/', views.transfer_create_view, name='transfer_create'),
    path('transfers/<int:pk>/', views.transfer_detail_view, name='transfer_detail'),
    path('transfers/<int:pk>/edit/', views.transfer_edit_view, name='transfer_edit'),
    path('transfers/<int:pk>/delete/', views.transfer_delete_view, name='transfer_delete'),
    path('transfers/<int:pk>/submit/', views.transfer_submit_view, name='transfer_submit'),
    path('transfers/<int:pk>/approve/', views.transfer_approve_view, name='transfer_approve'),
    path('transfers/<int:pk>/receive/', views.transfer_receive_view, name='transfer_receive'),
    path('transfers/<int:pk>/cancel/', views.transfer_cancel_view, name='transfer_cancel'),

    # Stock Adjustments
    path('adjustments/', views.adjustment_list_view, name='adjustment_list'),
    path('adjustments/add/', views.adjustment_create_view, name='adjustment_create'),
    path('adjustments/<int:pk>/', views.adjustment_detail_view, name='adjustment_detail'),
    path('adjustments/<int:pk>/edit/', views.adjustment_edit_view, name='adjustment_edit'),
    path('adjustments/<int:pk>/delete/', views.adjustment_delete_view, name='adjustment_delete'),
    path('adjustments/<int:pk>/submit/', views.adjustment_submit_view, name='adjustment_submit'),
    path('adjustments/<int:pk>/approve/', views.adjustment_approve_view, name='adjustment_approve'),
    path('adjustments/<int:pk>/reject/', views.adjustment_reject_view, name='adjustment_reject'),

    # Reorder Rules
    path('reorder-rules/', views.reorder_rule_list_view, name='reorder_rule_list'),
    path('reorder-rules/add/', views.reorder_rule_create_view, name='reorder_rule_create'),
    path('reorder-rules/<int:pk>/edit/', views.reorder_rule_edit_view, name='reorder_rule_edit'),
    path('reorder-rules/<int:pk>/delete/', views.reorder_rule_delete_view, name='reorder_rule_delete'),

    # Reorder Suggestions
    path('reorder-suggestions/', views.reorder_suggestion_list_view, name='reorder_suggestion_list'),
    path('reorder-suggestions/generate/', views.reorder_suggestion_generate_view, name='reorder_suggestion_generate'),
    path('reorder-suggestions/<int:pk>/approve/', views.reorder_suggestion_approve_view, name='reorder_suggestion_approve'),
    path('reorder-suggestions/<int:pk>/dismiss/', views.reorder_suggestion_dismiss_view, name='reorder_suggestion_dismiss'),

    # Inventory Valuations
    path('valuations/', views.valuation_list_view, name='valuation_list'),
    path('valuations/add/', views.valuation_create_view, name='valuation_create'),
    path('valuations/<int:pk>/', views.valuation_detail_view, name='valuation_detail'),
    path('valuations/<int:pk>/run/', views.valuation_run_view, name='valuation_run'),
    path('valuations/<int:pk>/complete/', views.valuation_complete_view, name='valuation_complete'),
    path('valuations/<int:pk>/delete/', views.valuation_delete_view, name='valuation_delete'),
]
