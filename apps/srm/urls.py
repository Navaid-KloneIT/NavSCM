from django.urls import path

from . import views

app_name = 'srm'

urlpatterns = [
    # Supplier Onboarding
    path('onboardings/', views.onboarding_list_view, name='onboarding_list'),
    path('onboardings/add/', views.onboarding_create_view, name='onboarding_create'),
    path('onboardings/<int:pk>/', views.onboarding_detail_view, name='onboarding_detail'),
    path('onboardings/<int:pk>/edit/', views.onboarding_edit_view, name='onboarding_edit'),
    path('onboardings/<int:pk>/delete/', views.onboarding_delete_view, name='onboarding_delete'),

    # Qualification Questions
    path('questions/', views.question_list_view, name='question_list'),
    path('questions/add/', views.question_create_view, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit_view, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete_view, name='question_delete'),

    # Scorecard Periods
    path('periods/', views.period_list_view, name='period_list'),
    path('periods/add/', views.period_create_view, name='period_create'),
    path('periods/<int:pk>/edit/', views.period_edit_view, name='period_edit'),
    path('periods/<int:pk>/delete/', views.period_delete_view, name='period_delete'),

    # Supplier Scorecards
    path('scorecards/', views.scorecard_list_view, name='scorecard_list'),
    path('scorecards/add/', views.scorecard_create_view, name='scorecard_create'),
    path('scorecards/<int:pk>/', views.scorecard_detail_view, name='scorecard_detail'),
    path('scorecards/<int:pk>/edit/', views.scorecard_edit_view, name='scorecard_edit'),
    path('scorecards/<int:pk>/delete/', views.scorecard_delete_view, name='scorecard_delete'),

    # Supplier Contracts
    path('contracts/', views.contract_list_view, name='contract_list'),
    path('contracts/add/', views.contract_create_view, name='contract_create'),
    path('contracts/<int:pk>/', views.contract_detail_view, name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.contract_edit_view, name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.contract_delete_view, name='contract_delete'),

    # Supplier Catalogs
    path('catalogs/', views.catalog_list_view, name='catalog_list'),
    path('catalogs/add/', views.catalog_create_view, name='catalog_create'),
    path('catalogs/<int:pk>/', views.catalog_detail_view, name='catalog_detail'),
    path('catalogs/<int:pk>/edit/', views.catalog_edit_view, name='catalog_edit'),
    path('catalogs/<int:pk>/delete/', views.catalog_delete_view, name='catalog_delete'),

    # Risk Assessments
    path('risks/', views.risk_list_view, name='risk_list'),
    path('risks/add/', views.risk_create_view, name='risk_create'),
    path('risks/<int:pk>/', views.risk_detail_view, name='risk_detail'),
    path('risks/<int:pk>/edit/', views.risk_edit_view, name='risk_edit'),
    path('risks/<int:pk>/delete/', views.risk_delete_view, name='risk_delete'),
]
