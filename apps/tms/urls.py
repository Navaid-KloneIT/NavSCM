from django.urls import path

from . import views

app_name = 'tms'

urlpatterns = [
    # =========================================================================
    # CARRIER MANAGEMENT
    # =========================================================================
    path('carriers/', views.carrier_list_view, name='carrier_list'),
    path('carriers/add/', views.carrier_create_view, name='carrier_create'),
    path('carriers/<int:pk>/', views.carrier_detail_view, name='carrier_detail'),
    path('carriers/<int:pk>/edit/', views.carrier_edit_view, name='carrier_edit'),
    path('carriers/<int:pk>/delete/', views.carrier_delete_view, name='carrier_delete'),

    # =========================================================================
    # RATE CARDS
    # =========================================================================
    path('rates/', views.rate_list_view, name='rate_list'),
    path('rates/add/', views.rate_create_view, name='rate_create'),
    path('rates/<int:pk>/', views.rate_detail_view, name='rate_detail'),
    path('rates/<int:pk>/edit/', views.rate_edit_view, name='rate_edit'),
    path('rates/<int:pk>/delete/', views.rate_delete_view, name='rate_delete'),

    # =========================================================================
    # ROUTE PLANNING
    # =========================================================================
    path('routes/', views.route_list_view, name='route_list'),
    path('routes/add/', views.route_create_view, name='route_create'),
    path('routes/<int:pk>/', views.route_detail_view, name='route_detail'),
    path('routes/<int:pk>/edit/', views.route_edit_view, name='route_edit'),
    path('routes/<int:pk>/delete/', views.route_delete_view, name='route_delete'),
    path('routes/<int:pk>/activate/', views.route_activate_view, name='route_activate'),
    path('routes/<int:pk>/deactivate/', views.route_deactivate_view, name='route_deactivate'),

    # =========================================================================
    # SHIPMENTS
    # =========================================================================
    path('shipments/', views.shipment_list_view, name='shipment_list'),
    path('shipments/add/', views.shipment_create_view, name='shipment_create'),
    path('shipments/<int:pk>/', views.shipment_detail_view, name='shipment_detail'),
    path('shipments/<int:pk>/edit/', views.shipment_edit_view, name='shipment_edit'),
    path('shipments/<int:pk>/delete/', views.shipment_delete_view, name='shipment_delete'),
    path('shipments/<int:pk>/book/', views.shipment_book_view, name='shipment_book'),
    path('shipments/<int:pk>/pickup/', views.shipment_pickup_view, name='shipment_pickup'),
    path('shipments/<int:pk>/transit/', views.shipment_transit_view, name='shipment_transit'),
    path('shipments/<int:pk>/deliver/', views.shipment_deliver_view, name='shipment_deliver'),
    path('shipments/<int:pk>/cancel/', views.shipment_cancel_view, name='shipment_cancel'),

    # =========================================================================
    # SHIPMENT TRACKING
    # =========================================================================
    path('tracking/', views.tracking_list_view, name='tracking_list'),
    path('tracking/<int:pk>/', views.tracking_detail_view, name='tracking_detail'),
    path('tracking/add/<int:shipment_pk>/', views.tracking_add_view, name='tracking_add'),

    # =========================================================================
    # FREIGHT AUDIT & PAYMENT
    # =========================================================================
    path('freight/', views.freight_list_view, name='freight_list'),
    path('freight/add/', views.freight_create_view, name='freight_create'),
    path('freight/<int:pk>/', views.freight_detail_view, name='freight_detail'),
    path('freight/<int:pk>/edit/', views.freight_edit_view, name='freight_edit'),
    path('freight/<int:pk>/delete/', views.freight_delete_view, name='freight_delete'),
    path('freight/<int:pk>/submit/', views.freight_submit_view, name='freight_submit'),
    path('freight/<int:pk>/approve/', views.freight_approve_view, name='freight_approve'),
    path('freight/<int:pk>/dispute/', views.freight_dispute_view, name='freight_dispute'),
    path('freight/<int:pk>/pay/', views.freight_pay_view, name='freight_pay'),
    path('freight/<int:pk>/cancel/', views.freight_cancel_view, name='freight_cancel'),

    # =========================================================================
    # LOAD OPTIMIZATION
    # =========================================================================
    path('loads/', views.load_list_view, name='load_list'),
    path('loads/add/', views.load_create_view, name='load_create'),
    path('loads/<int:pk>/', views.load_detail_view, name='load_detail'),
    path('loads/<int:pk>/edit/', views.load_edit_view, name='load_edit'),
    path('loads/<int:pk>/delete/', views.load_delete_view, name='load_delete'),
    path('loads/<int:pk>/plan/', views.load_plan_view, name='load_plan'),
    path('loads/<int:pk>/start/', views.load_start_view, name='load_start'),
    path('loads/<int:pk>/complete/', views.load_complete_view, name='load_complete'),
    path('loads/<int:pk>/close/', views.load_close_view, name='load_close'),
]
