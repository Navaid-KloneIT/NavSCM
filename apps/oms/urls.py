from django.urls import path

from . import views

app_name = 'oms'

urlpatterns = [
    # =========================================================================
    # CUSTOMER MANAGEMENT
    # =========================================================================
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/add/', views.customer_create_view, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail_view, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit_view, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete_view, name='customer_delete'),

    # =========================================================================
    # SALES CHANNELS
    # =========================================================================
    path('channels/', views.channel_list_view, name='channel_list'),
    path('channels/add/', views.channel_create_view, name='channel_create'),
    path('channels/<int:pk>/edit/', views.channel_edit_view, name='channel_edit'),
    path('channels/<int:pk>/delete/', views.channel_delete_view, name='channel_delete'),

    # =========================================================================
    # ORDERS
    # =========================================================================
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/add/', views.order_create_view, name='order_create'),
    path('orders/<int:pk>/', views.order_detail_view, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_edit_view, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete_view, name='order_delete'),
    path('orders/<int:pk>/submit-validation/', views.order_submit_validation_view, name='order_submit_validation'),
    path('orders/<int:pk>/validate/', views.order_validate_view, name='order_validate'),
    path('orders/<int:pk>/allocate/', views.order_allocate_view, name='order_allocate'),
    path('orders/<int:pk>/fulfill/', views.order_fulfill_view, name='order_fulfill'),
    path('orders/<int:pk>/ship/', views.order_ship_view, name='order_ship'),
    path('orders/<int:pk>/deliver/', views.order_deliver_view, name='order_deliver'),
    path('orders/<int:pk>/cancel/', views.order_cancel_view, name='order_cancel'),
    path('orders/<int:pk>/hold/', views.order_hold_view, name='order_hold'),
    path('orders/<int:pk>/release/', views.order_release_view, name='order_release'),

    # =========================================================================
    # ORDER VALIDATIONS
    # =========================================================================
    path('validations/', views.validation_list_view, name='validation_list'),
    path('validations/<int:pk>/', views.validation_detail_view, name='validation_detail'),
    path('validations/<int:pk>/pass/', views.validation_pass_view, name='validation_pass'),
    path('validations/<int:pk>/fail/', views.validation_fail_view, name='validation_fail'),

    # =========================================================================
    # ORDER ALLOCATIONS
    # =========================================================================
    path('allocations/', views.allocation_list_view, name='allocation_list'),
    path('allocations/add/', views.allocation_create_view, name='allocation_create'),
    path('allocations/<int:pk>/', views.allocation_detail_view, name='allocation_detail'),
    path('allocations/<int:pk>/confirm/', views.allocation_confirm_view, name='allocation_confirm'),
    path('allocations/<int:pk>/delete/', views.allocation_delete_view, name='allocation_delete'),

    # =========================================================================
    # BACKORDERS
    # =========================================================================
    path('backorders/', views.backorder_list_view, name='backorder_list'),
    path('backorders/<int:pk>/', views.backorder_detail_view, name='backorder_detail'),
    path('backorders/<int:pk>/fulfill/', views.backorder_fulfill_view, name='backorder_fulfill'),
    path('backorders/<int:pk>/cancel/', views.backorder_cancel_view, name='backorder_cancel'),

    # =========================================================================
    # CUSTOMER NOTIFICATIONS
    # =========================================================================
    path('notifications/', views.notification_list_view, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail_view, name='notification_detail'),
    path('notifications/<int:pk>/send/', views.notification_send_view, name='notification_send'),
]
