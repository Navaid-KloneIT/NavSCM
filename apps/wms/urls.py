from django.urls import path

from . import views

app_name = 'wms'

urlpatterns = [
    # =========================================================================
    # BIN MANAGEMENT
    # =========================================================================
    path('bins/', views.bin_list_view, name='bin_list'),
    path('bins/add/', views.bin_create_view, name='bin_create'),
    path('bins/<int:pk>/', views.bin_detail_view, name='bin_detail'),
    path('bins/<int:pk>/edit/', views.bin_edit_view, name='bin_edit'),
    path('bins/<int:pk>/delete/', views.bin_delete_view, name='bin_delete'),

    # =========================================================================
    # DOCK APPOINTMENTS
    # =========================================================================
    path('dock-appointments/', views.dock_list_view, name='dock_list'),
    path('dock-appointments/add/', views.dock_create_view, name='dock_create'),
    path('dock-appointments/<int:pk>/', views.dock_detail_view, name='dock_detail'),
    path('dock-appointments/<int:pk>/edit/', views.dock_edit_view, name='dock_edit'),
    path('dock-appointments/<int:pk>/delete/', views.dock_delete_view, name='dock_delete'),
    path('dock-appointments/<int:pk>/check-in/', views.dock_check_in_view, name='dock_check_in'),
    path('dock-appointments/<int:pk>/complete/', views.dock_complete_view, name='dock_complete'),
    path('dock-appointments/<int:pk>/cancel/', views.dock_cancel_view, name='dock_cancel'),

    # =========================================================================
    # RECEIVING ORDERS
    # =========================================================================
    path('receiving/', views.receiving_list_view, name='receiving_list'),
    path('receiving/add/', views.receiving_create_view, name='receiving_create'),
    path('receiving/<int:pk>/', views.receiving_detail_view, name='receiving_detail'),
    path('receiving/<int:pk>/edit/', views.receiving_edit_view, name='receiving_edit'),
    path('receiving/<int:pk>/delete/', views.receiving_delete_view, name='receiving_delete'),
    path('receiving/<int:pk>/start/', views.receiving_start_view, name='receiving_start'),
    path('receiving/<int:pk>/complete/', views.receiving_complete_view, name='receiving_complete'),

    # =========================================================================
    # PUT-AWAY TASKS
    # =========================================================================
    path('put-away/', views.putaway_list_view, name='putaway_list'),
    path('put-away/<int:pk>/', views.putaway_detail_view, name='putaway_detail'),
    path('put-away/<int:pk>/start/', views.putaway_start_view, name='putaway_start'),
    path('put-away/<int:pk>/complete/', views.putaway_complete_view, name='putaway_complete'),

    # =========================================================================
    # PICK LISTS
    # =========================================================================
    path('pick-lists/', views.picklist_list_view, name='picklist_list'),
    path('pick-lists/add/', views.picklist_create_view, name='picklist_create'),
    path('pick-lists/<int:pk>/', views.picklist_detail_view, name='picklist_detail'),
    path('pick-lists/<int:pk>/edit/', views.picklist_edit_view, name='picklist_edit'),
    path('pick-lists/<int:pk>/delete/', views.picklist_delete_view, name='picklist_delete'),
    path('pick-lists/<int:pk>/start/', views.picklist_start_view, name='picklist_start'),
    path('pick-lists/<int:pk>/complete/', views.picklist_complete_view, name='picklist_complete'),

    # =========================================================================
    # PACKING ORDERS
    # =========================================================================
    path('packing/', views.packing_list_view, name='packing_list'),
    path('packing/add/', views.packing_create_view, name='packing_create'),
    path('packing/<int:pk>/', views.packing_detail_view, name='packing_detail'),
    path('packing/<int:pk>/edit/', views.packing_edit_view, name='packing_edit'),
    path('packing/<int:pk>/delete/', views.packing_delete_view, name='packing_delete'),
    path('packing/<int:pk>/start/', views.packing_start_view, name='packing_start'),
    path('packing/<int:pk>/complete/', views.packing_complete_view, name='packing_complete'),
    path('packing/<int:pk>/ship/', views.packing_ship_view, name='packing_ship'),

    # =========================================================================
    # SHIPPING LABELS
    # =========================================================================
    path('shipping-labels/', views.label_list_view, name='label_list'),
    path('shipping-labels/<int:pk>/', views.label_detail_view, name='label_detail'),
    path('shipping-labels/generate/<int:packing_pk>/', views.label_generate_view, name='label_generate'),

    # =========================================================================
    # CYCLE COUNT PLANS
    # =========================================================================
    path('cycle-count-plans/', views.plan_list_view, name='plan_list'),
    path('cycle-count-plans/add/', views.plan_create_view, name='plan_create'),
    path('cycle-count-plans/<int:pk>/', views.plan_detail_view, name='plan_detail'),
    path('cycle-count-plans/<int:pk>/edit/', views.plan_edit_view, name='plan_edit'),
    path('cycle-count-plans/<int:pk>/delete/', views.plan_delete_view, name='plan_delete'),
    path('cycle-count-plans/<int:pk>/activate/', views.plan_activate_view, name='plan_activate'),
    path('cycle-count-plans/<int:pk>/pause/', views.plan_pause_view, name='plan_pause'),

    # =========================================================================
    # CYCLE COUNTS
    # =========================================================================
    path('cycle-counts/', views.count_list_view, name='count_list'),
    path('cycle-counts/add/', views.count_create_view, name='count_create'),
    path('cycle-counts/<int:pk>/', views.count_detail_view, name='count_detail'),
    path('cycle-counts/<int:pk>/start/', views.count_start_view, name='count_start'),
    path('cycle-counts/<int:pk>/complete/', views.count_complete_view, name='count_complete'),

    # =========================================================================
    # YARD LOCATIONS
    # =========================================================================
    path('yard-locations/', views.yard_location_list_view, name='yard_location_list'),
    path('yard-locations/add/', views.yard_location_create_view, name='yard_location_create'),
    path('yard-locations/<int:pk>/', views.yard_location_detail_view, name='yard_location_detail'),
    path('yard-locations/<int:pk>/edit/', views.yard_location_edit_view, name='yard_location_edit'),
    path('yard-locations/<int:pk>/delete/', views.yard_location_delete_view, name='yard_location_delete'),

    # =========================================================================
    # YARD VISITS
    # =========================================================================
    path('yard-visits/', views.yard_visit_list_view, name='yard_visit_list'),
    path('yard-visits/add/', views.yard_visit_create_view, name='yard_visit_create'),
    path('yard-visits/<int:pk>/', views.yard_visit_detail_view, name='yard_visit_detail'),
    path('yard-visits/<int:pk>/check-in/', views.yard_visit_check_in_view, name='yard_visit_check_in'),
    path('yard-visits/<int:pk>/dock/', views.yard_visit_dock_view, name='yard_visit_dock'),
    path('yard-visits/<int:pk>/complete/', views.yard_visit_complete_view, name='yard_visit_complete'),
    path('yard-visits/<int:pk>/depart/', views.yard_visit_depart_view, name='yard_visit_depart'),
]
