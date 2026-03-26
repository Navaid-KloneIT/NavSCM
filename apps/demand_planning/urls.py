from django.urls import path

from . import views

app_name = 'demand_planning'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Sales Forecasts
    # -------------------------------------------------------------------------
    path('forecasts/', views.forecast_list_view, name='forecast_list'),
    path('forecasts/add/', views.forecast_create_view, name='forecast_create'),
    path('forecasts/<int:pk>/', views.forecast_detail_view, name='forecast_detail'),
    path('forecasts/<int:pk>/edit/', views.forecast_edit_view, name='forecast_edit'),
    path('forecasts/<int:pk>/delete/', views.forecast_delete_view, name='forecast_delete'),
    path('forecasts/<int:pk>/submit/', views.forecast_submit_view, name='forecast_submit'),
    path('forecasts/<int:pk>/approve/', views.forecast_approve_view, name='forecast_approve'),
    path('forecasts/<int:pk>/activate/', views.forecast_activate_view, name='forecast_activate'),
    path('forecasts/<int:pk>/archive/', views.forecast_archive_view, name='forecast_archive'),

    # -------------------------------------------------------------------------
    # Seasonality Profiles
    # -------------------------------------------------------------------------
    path('seasonality/', views.seasonality_list_view, name='seasonality_list'),
    path('seasonality/add/', views.seasonality_create_view, name='seasonality_create'),
    path('seasonality/<int:pk>/', views.seasonality_detail_view, name='seasonality_detail'),
    path('seasonality/<int:pk>/edit/', views.seasonality_edit_view, name='seasonality_edit'),
    path('seasonality/<int:pk>/delete/', views.seasonality_delete_view, name='seasonality_delete'),

    # -------------------------------------------------------------------------
    # Promotional Events
    # -------------------------------------------------------------------------
    path('events/', views.event_list_view, name='event_list'),
    path('events/add/', views.event_create_view, name='event_create'),
    path('events/<int:pk>/edit/', views.event_edit_view, name='event_edit'),
    path('events/<int:pk>/delete/', views.event_delete_view, name='event_delete'),

    # -------------------------------------------------------------------------
    # Demand Signals
    # -------------------------------------------------------------------------
    path('signals/', views.signal_list_view, name='signal_list'),
    path('signals/add/', views.signal_create_view, name='signal_create'),
    path('signals/<int:pk>/', views.signal_detail_view, name='signal_detail'),
    path('signals/<int:pk>/edit/', views.signal_edit_view, name='signal_edit'),
    path('signals/<int:pk>/delete/', views.signal_delete_view, name='signal_delete'),
    path('signals/<int:pk>/analyze/', views.signal_analyze_view, name='signal_analyze'),
    path('signals/<int:pk>/incorporate/', views.signal_incorporate_view, name='signal_incorporate'),
    path('signals/<int:pk>/dismiss/', views.signal_dismiss_view, name='signal_dismiss'),

    # -------------------------------------------------------------------------
    # Collaborative Plans
    # -------------------------------------------------------------------------
    path('plans/', views.plan_list_view, name='plan_list'),
    path('plans/add/', views.plan_create_view, name='plan_create'),
    path('plans/<int:pk>/', views.plan_detail_view, name='plan_detail'),
    path('plans/<int:pk>/edit/', views.plan_edit_view, name='plan_edit'),
    path('plans/<int:pk>/delete/', views.plan_delete_view, name='plan_delete'),
    path('plans/<int:pk>/submit/', views.plan_submit_view, name='plan_submit'),
    path('plans/<int:pk>/approve/', views.plan_approve_view, name='plan_approve'),
    path('plans/<int:pk>/finalize/', views.plan_finalize_view, name='plan_finalize'),
    path('plans/<int:pk>/comment/', views.plan_comment_view, name='plan_comment'),

    # -------------------------------------------------------------------------
    # Safety Stock Calculations
    # -------------------------------------------------------------------------
    path('safety-stock/', views.safety_stock_list_view, name='safety_stock_list'),
    path('safety-stock/add/', views.safety_stock_create_view, name='safety_stock_create'),
    path('safety-stock/<int:pk>/', views.safety_stock_detail_view, name='safety_stock_detail'),
    path('safety-stock/<int:pk>/edit/', views.safety_stock_edit_view, name='safety_stock_edit'),
    path('safety-stock/<int:pk>/delete/', views.safety_stock_delete_view, name='safety_stock_delete'),
    path('safety-stock/<int:pk>/calculate/', views.safety_stock_calculate_view, name='safety_stock_calculate'),
    path('safety-stock/<int:pk>/approve/', views.safety_stock_approve_view, name='safety_stock_approve'),
    path('safety-stock/<int:pk>/apply/', views.safety_stock_apply_view, name='safety_stock_apply'),
]
