import json

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.shortcuts import render

from apps.accounts.models import Role, User, UserInvite
from apps.inventory.models import StockItem, Warehouse
from apps.oms.models import Customer, Order
from apps.procurement.models import PurchaseOrder, PurchaseRequisition, Vendor
from apps.srm.models import SupplierContract, SupplierOnboarding
from apps.tms.models import Carrier, FreightBill, Shipment
from apps.wms.models import ReceivingOrder


@login_required
def dashboard_view(request):
    tenant = getattr(request, 'tenant', None)

    if tenant:
        # =================================================================
        # ADMINISTRATION
        # =================================================================
        total_users = User.objects.filter(tenant=tenant).count()
        active_users = User.objects.filter(tenant=tenant, is_active=True).count()
        pending_invites = UserInvite.objects.filter(tenant=tenant, status='pending').count()
        total_roles = Role.objects.filter(tenant=tenant).count()
        recent_users = User.objects.filter(tenant=tenant).order_by('-date_joined')[:5]
        recent_invites = UserInvite.objects.filter(tenant=tenant).order_by('-created_at')[:5]

        # =================================================================
        # PROCUREMENT
        # =================================================================
        total_vendors = Vendor.objects.filter(tenant=tenant, is_active=True).count()
        open_pos = PurchaseOrder.objects.filter(
            tenant=tenant
        ).exclude(status__in=['received', 'cancelled']).count()
        pending_requisitions = PurchaseRequisition.objects.filter(
            tenant=tenant, status='pending_approval'
        ).count()

        # PO status breakdown
        po_by_status = list(
            PurchaseOrder.objects.filter(tenant=tenant)
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # =================================================================
        # SRM
        # =================================================================
        approved_onboardings = SupplierOnboarding.objects.filter(
            tenant=tenant, status='approved'
        ).count()
        active_contracts = SupplierContract.objects.filter(
            tenant=tenant, status='active'
        ).count()

        # =================================================================
        # INVENTORY
        # =================================================================
        total_warehouses = Warehouse.objects.filter(tenant=tenant, is_active=True).count()
        low_stock_count = StockItem.objects.filter(
            tenant=tenant,
            reorder_point__gt=0,
            quantity_on_hand__lte=F('reorder_point'),
        ).count()

        # =================================================================
        # WMS
        # =================================================================
        pending_receiving = ReceivingOrder.objects.filter(
            tenant=tenant, status__in=['pending', 'in_progress']
        ).count()

        # =================================================================
        # OMS
        # =================================================================
        total_orders = Order.objects.filter(tenant=tenant).count()
        total_customers = Customer.objects.filter(tenant=tenant, is_active=True).count()
        recent_orders = Order.objects.filter(
            tenant=tenant
        ).select_related('customer').order_by('-created_at')[:5]

        # Order status breakdown
        order_by_status = list(
            Order.objects.filter(tenant=tenant)
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # =================================================================
        # TMS
        # =================================================================
        active_shipments = Shipment.objects.filter(
            tenant=tenant,
            status__in=['booked', 'picked_up', 'in_transit', 'at_hub', 'out_for_delivery'],
        ).count()
        total_carriers = Carrier.objects.filter(tenant=tenant, is_active=True).count()
        recent_shipments = Shipment.objects.filter(
            tenant=tenant
        ).select_related('carrier').order_by('-created_at')[:5]

        # Shipment status breakdown
        shipment_by_status = list(
            Shipment.objects.filter(tenant=tenant)
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # Freight bill status breakdown
        freight_by_status = list(
            FreightBill.objects.filter(tenant=tenant)
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

    else:
        # Superuser with no tenant - show zeroes
        total_users = active_users = pending_invites = total_roles = 0
        recent_users = recent_invites = []
        total_vendors = open_pos = pending_requisitions = 0
        po_by_status = []
        approved_onboardings = active_contracts = 0
        total_warehouses = low_stock_count = 0
        pending_receiving = 0
        total_orders = total_customers = 0
        recent_orders = []
        order_by_status = []
        active_shipments = total_carriers = 0
        recent_shipments = []
        shipment_by_status = freight_by_status = []

    # =================================================================
    # CHART DATA (JSON for ApexCharts)
    # =================================================================

    # Status label mapping for display
    po_status_labels = {
        'draft': 'Draft', 'pending_approval': 'Pending', 'approved': 'Approved',
        'sent': 'Sent', 'acknowledged': 'Acknowledged',
        'partially_received': 'Partial', 'received': 'Received', 'cancelled': 'Cancelled',
    }
    order_status_labels = {
        'draft': 'Draft', 'pending_validation': 'Pending', 'validated': 'Validated',
        'allocated': 'Allocated', 'in_fulfillment': 'Fulfilling',
        'partially_shipped': 'Partial Ship', 'shipped': 'Shipped',
        'delivered': 'Delivered', 'cancelled': 'Cancelled', 'on_hold': 'On Hold',
    }
    shipment_status_labels = {
        'draft': 'Draft', 'booked': 'Booked', 'picked_up': 'Picked Up',
        'in_transit': 'In Transit', 'at_hub': 'At Hub',
        'out_for_delivery': 'Out for Delivery', 'delivered': 'Delivered',
        'failed': 'Failed', 'cancelled': 'Cancelled',
    }
    freight_status_labels = {
        'draft': 'Draft', 'pending_review': 'Pending', 'approved': 'Approved',
        'disputed': 'Disputed', 'paid': 'Paid', 'cancelled': 'Cancelled',
    }

    # Build chart JSON
    po_chart_labels = json.dumps([po_status_labels.get(s['status'], s['status'].title()) for s in po_by_status])
    po_chart_data = json.dumps([s['count'] for s in po_by_status])

    order_chart_labels = json.dumps([order_status_labels.get(s['status'], s['status'].title()) for s in order_by_status])
    order_chart_data = json.dumps([s['count'] for s in order_by_status])

    shipment_chart_labels = json.dumps([shipment_status_labels.get(s['status'], s['status'].title()) for s in shipment_by_status])
    shipment_chart_data = json.dumps([s['count'] for s in shipment_by_status])

    freight_chart_labels = json.dumps([freight_status_labels.get(s['status'], s['status'].title()) for s in freight_by_status])
    freight_chart_data = json.dumps([s['count'] for s in freight_by_status])

    # Module overview bar chart
    module_bar_labels = json.dumps(['Vendors', 'Suppliers', 'Warehouses', 'Orders', 'Shipments', 'Carriers'])
    module_bar_data = json.dumps([total_vendors, approved_onboardings, total_warehouses, total_orders, active_shipments, total_carriers])

    context = {
        # Administration
        'total_users': total_users,
        'active_users': active_users,
        'pending_invites': pending_invites,
        'total_roles': total_roles,
        'recent_users': recent_users,
        'recent_invites': recent_invites,
        # Procurement
        'total_vendors': total_vendors,
        'open_pos': open_pos,
        'pending_requisitions': pending_requisitions,
        'po_by_status': po_by_status,
        # SRM
        'approved_onboardings': approved_onboardings,
        'active_contracts': active_contracts,
        # Inventory
        'total_warehouses': total_warehouses,
        'low_stock_count': low_stock_count,
        # WMS
        'pending_receiving': pending_receiving,
        # OMS
        'total_orders': total_orders,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'order_by_status': order_by_status,
        # TMS
        'active_shipments': active_shipments,
        'total_carriers': total_carriers,
        'recent_shipments': recent_shipments,
        'shipment_by_status': shipment_by_status,
        'freight_by_status': freight_by_status,
        # Chart JSON
        'po_chart_labels': po_chart_labels,
        'po_chart_data': po_chart_data,
        'order_chart_labels': order_chart_labels,
        'order_chart_data': order_chart_data,
        'shipment_chart_labels': shipment_chart_labels,
        'shipment_chart_data': shipment_chart_data,
        'freight_chart_labels': freight_chart_labels,
        'freight_chart_data': freight_chart_data,
        'module_bar_labels': module_bar_labels,
        'module_bar_data': module_bar_data,
    }

    return render(request, 'dashboard/index.html', context)
