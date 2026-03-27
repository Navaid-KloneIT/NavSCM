import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.inventory.models import Warehouse
from apps.manufacturing.models import (
    BillOfMaterials,
    BOMLineItem,
    MRPRequirement,
    MRPRun,
    ProductionLog,
    ProductionSchedule,
    ProductionScheduleItem,
    WorkCenter,
    WorkOrder,
    WorkOrderOperation,
)
from apps.procurement.models import Item

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample manufacturing data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing manufacturing data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing manufacturing data...'))
            ProductionLog.objects.all().delete()
            MRPRequirement.objects.all().delete()
            MRPRun.objects.all().delete()
            WorkOrderOperation.objects.all().delete()
            WorkOrder.objects.all().delete()
            ProductionScheduleItem.objects.all().delete()
            ProductionSchedule.objects.all().delete()
            BOMLineItem.objects.all().delete()
            BillOfMaterials.objects.all().delete()
            WorkCenter.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All manufacturing data flushed.'))

        for tenant in tenants:
            self.stdout.write(f'\nSeeding manufacturing data for: {tenant.name}')
            users = list(User.objects.filter(tenant=tenant, is_active=True))

            if not users:
                self.stdout.write(self.style.WARNING('  No users found, skipping.'))
                continue

            items = list(Item.objects.filter(tenant=tenant, is_active=True))
            if not items:
                self.stdout.write(self.style.WARNING(
                    '  No items found. Run "python manage.py seed_procurement" first.'
                ))
                continue

            warehouses = list(Warehouse.objects.filter(tenant=tenant, is_active=True))
            if not warehouses:
                self.stdout.write(self.style.WARNING(
                    '  No warehouses found. Run "python manage.py seed_inventory" first.'
                ))
                continue

            if WorkCenter.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    '  Manufacturing data already exists. Use --flush to re-seed.'
                ))
                continue

            work_centers = self._create_work_centers(tenant)
            boms = self._create_boms(tenant, users, items)
            schedules = self._create_production_schedules(tenant, users, items, boms, work_centers)
            work_orders = self._create_work_orders(tenant, users, items, boms, schedules, work_centers)
            self._create_mrp_runs(tenant, users, items, warehouses)
            self._create_production_logs(tenant, users, work_orders, work_centers)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Manufacturing seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Log in as a tenant admin (e.g., admin_<slug>) to see module data.'
        ))
        self.stdout.write(self.style.WARNING(
            'Superuser "admin" has no tenant — data will not appear.'
        ))

    # -------------------------------------------------------------------------
    # WORK CENTERS
    # -------------------------------------------------------------------------
    def _create_work_centers(self, tenant):
        work_centers_data = [
            {
                'code': 'WC-001',
                'name': 'CNC Machine',
                'work_center_type': 'machine',
                'hourly_capacity': Decimal('8.00'),
                'cost_per_hour': Decimal('120.00'),
                'location': 'Building A, Floor 1',
                'description': 'High-precision CNC machining center for metal parts.',
            },
            {
                'code': 'WC-002',
                'name': 'Assembly Line A',
                'work_center_type': 'assembly_line',
                'hourly_capacity': Decimal('25.00'),
                'cost_per_hour': Decimal('85.00'),
                'location': 'Building B, Floor 1',
                'description': 'Main product assembly line with 12 stations.',
            },
            {
                'code': 'WC-003',
                'name': 'Manual Station 1',
                'work_center_type': 'manual_station',
                'hourly_capacity': Decimal('4.00'),
                'cost_per_hour': Decimal('45.00'),
                'location': 'Building A, Floor 2',
                'description': 'Manual workstation for custom assembly and rework.',
            },
            {
                'code': 'WC-004',
                'name': 'QC Testing',
                'work_center_type': 'testing_station',
                'hourly_capacity': Decimal('15.00'),
                'cost_per_hour': Decimal('65.00'),
                'location': 'Building C, Floor 1',
                'description': 'Quality control and testing lab for finished goods.',
            },
            {
                'code': 'WC-005',
                'name': 'Packaging Station',
                'work_center_type': 'packaging',
                'hourly_capacity': Decimal('30.00'),
                'cost_per_hour': Decimal('35.00'),
                'location': 'Building B, Floor 2',
                'description': 'Final packaging and labeling station.',
            },
        ]

        results = []
        for data in work_centers_data:
            wc, created = WorkCenter.objects.get_or_create(
                tenant=tenant,
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'work_center_type': data['work_center_type'],
                    'hourly_capacity': data['hourly_capacity'],
                    'cost_per_hour': data['cost_per_hour'],
                    'is_active': True,
                    'location': data['location'],
                    'description': data['description'],
                },
            )
            results.append(wc)
        self.stdout.write(f'  Created {len(results)} work centers')
        return results

    # -------------------------------------------------------------------------
    # BILLS OF MATERIALS
    # -------------------------------------------------------------------------
    def _create_boms(self, tenant, users, items):
        # We need at least 4 "product" items and several "component" items
        product_items = items[:min(len(items), 4)]
        component_items = items[:min(len(items), 10)]

        boms_data = [
            {
                'title': 'Standard Widget Assembly',
                'status': 'active',
                'version': '2.1',
                'yield_quantity': Decimal('1.00'),
                'notes': 'Standard widget with all components. Approved for production.',
                'line_items': [
                    {'uom': 'piece', 'qty': Decimal('4.00'), 'scrap': Decimal('2.00'), 'notes': 'Main body component'},
                    {'uom': 'piece', 'qty': Decimal('8.00'), 'scrap': Decimal('1.50'), 'notes': 'Fastener set'},
                    {'uom': 'kg', 'qty': Decimal('0.50'), 'scrap': Decimal('5.00'), 'notes': 'Raw material filler'},
                    {'uom': 'piece', 'qty': Decimal('2.00'), 'scrap': Decimal('0.00'), 'notes': 'Electronic module'},
                    {'uom': 'set', 'qty': Decimal('1.00'), 'scrap': Decimal('0.00'), 'notes': 'Packaging kit'},
                ],
            },
            {
                'title': 'Premium Product Build',
                'status': 'active',
                'version': '1.3',
                'yield_quantity': Decimal('1.00'),
                'notes': 'Premium product configuration with enhanced materials.',
                'line_items': [
                    {'uom': 'piece', 'qty': Decimal('2.00'), 'scrap': Decimal('3.00'), 'notes': 'Premium housing'},
                    {'uom': 'kg', 'qty': Decimal('1.20'), 'scrap': Decimal('4.00'), 'notes': 'Specialty alloy'},
                    {'uom': 'piece', 'qty': Decimal('6.00'), 'scrap': Decimal('2.50'), 'notes': 'Precision screws'},
                    {'uom': 'meter', 'qty': Decimal('3.00'), 'scrap': Decimal('10.00'), 'notes': 'Wiring harness'},
                ],
            },
            {
                'title': 'Economy Line Assembly',
                'status': 'draft',
                'version': '0.5',
                'yield_quantity': Decimal('2.00'),
                'notes': 'Draft BOM for new economy product line. Pending review.',
                'line_items': [
                    {'uom': 'piece', 'qty': Decimal('3.00'), 'scrap': Decimal('5.00'), 'notes': 'Basic housing'},
                    {'uom': 'piece', 'qty': Decimal('4.00'), 'scrap': Decimal('2.00'), 'notes': 'Standard fasteners'},
                    {'uom': 'piece', 'qty': Decimal('1.00'), 'scrap': Decimal('0.00'), 'notes': 'Label sheet'},
                ],
            },
            {
                'title': 'Legacy Product V1 (Discontinued)',
                'status': 'obsolete',
                'version': '5.0',
                'yield_quantity': Decimal('1.00'),
                'notes': 'Obsolete BOM for discontinued legacy product.',
                'line_items': [
                    {'uom': 'piece', 'qty': Decimal('5.00'), 'scrap': Decimal('3.00'), 'notes': 'Old-style casing'},
                    {'uom': 'kg', 'qty': Decimal('2.00'), 'scrap': Decimal('8.00'), 'notes': 'Deprecated material'},
                    {'uom': 'piece', 'qty': Decimal('10.00'), 'scrap': Decimal('1.00'), 'notes': 'Rivets (legacy)'},
                    {'uom': 'piece', 'qty': Decimal('1.00'), 'scrap': Decimal('0.00'), 'notes': 'Legacy circuit board'},
                    {'uom': 'box', 'qty': Decimal('1.00'), 'scrap': Decimal('0.00'), 'notes': 'Old packaging box'},
                ],
            },
        ]

        results = []
        for i, data in enumerate(boms_data):
            product = product_items[i % len(product_items)]
            user = random.choice(users)

            bom = BillOfMaterials(
                tenant=tenant,
                product=product,
                title=data['title'],
                version=data['version'],
                status=data['status'],
                yield_quantity=data['yield_quantity'],
                notes=data['notes'],
                created_by=user,
            )
            if data['status'] in ('active', 'obsolete'):
                bom.approved_by = random.choice(users)
            bom.save()

            for j, line_data in enumerate(data['line_items']):
                component = component_items[(i * 5 + j) % len(component_items)]
                BOMLineItem.objects.create(
                    bom=bom,
                    item=component,
                    quantity=line_data['qty'],
                    unit_of_measure=line_data['uom'],
                    scrap_percentage=line_data['scrap'],
                    notes=line_data['notes'],
                )
            results.append(bom)
        self.stdout.write(f'  Created {len(results)} bills of materials with line items')
        return results

    # -------------------------------------------------------------------------
    # PRODUCTION SCHEDULES
    # -------------------------------------------------------------------------
    def _create_production_schedules(self, tenant, users, items, boms, work_centers):
        now = timezone.now()
        today = now.date()
        product_items = items[:min(len(items), 6)]
        active_boms = [b for b in boms if b.status == 'active']

        schedules_data = [
            {
                'title': 'April 2026 Production Plan',
                'status': 'planned',
                'start_date': today + timedelta(days=3),
                'end_date': today + timedelta(days=33),
                'notes': 'Monthly production schedule for April. All lines confirmed.',
                'items': [
                    {'priority': 'high', 'qty': Decimal('500.00'), 'offset_start': 3, 'offset_end': 10},
                    {'priority': 'medium', 'qty': Decimal('300.00'), 'offset_start': 8, 'offset_end': 18},
                    {'priority': 'low', 'qty': Decimal('200.00'), 'offset_start': 15, 'offset_end': 30},
                ],
            },
            {
                'title': 'Q2 2026 Rush Orders',
                'status': 'in_progress',
                'start_date': today - timedelta(days=5),
                'end_date': today + timedelta(days=25),
                'notes': 'High-priority rush orders for Q2 delivery commitments.',
                'items': [
                    {'priority': 'urgent', 'qty': Decimal('150.00'), 'offset_start': -5, 'offset_end': 5},
                    {'priority': 'high', 'qty': Decimal('400.00'), 'offset_start': -2, 'offset_end': 15},
                ],
            },
        ]

        results = []
        for data in schedules_data:
            user = random.choice(users)
            schedule = ProductionSchedule(
                tenant=tenant,
                title=data['title'],
                status=data['status'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                notes=data['notes'],
                created_by=user,
            )
            schedule.save()

            for j, item_data in enumerate(data['items']):
                product = product_items[j % len(product_items)]
                bom = active_boms[j % len(active_boms)] if active_boms else None
                wc = work_centers[j % len(work_centers)]
                planned_start = now + timedelta(days=item_data['offset_start'])
                planned_end = now + timedelta(days=item_data['offset_end'])

                ProductionScheduleItem.objects.create(
                    schedule=schedule,
                    product=product,
                    bom=bom,
                    planned_quantity=item_data['qty'],
                    work_center=wc,
                    planned_start=planned_start,
                    planned_end=planned_end,
                    priority=item_data['priority'],
                    notes=f"Scheduled production of {product.name}",
                )
            results.append(schedule)
        self.stdout.write(f'  Created {len(results)} production schedules with items')
        return results

    # -------------------------------------------------------------------------
    # WORK ORDERS
    # -------------------------------------------------------------------------
    def _create_work_orders(self, tenant, users, items, boms, schedules, work_centers):
        now = timezone.now()
        today = now.date()
        product_items = items[:min(len(items), 6)]
        active_boms = [b for b in boms if b.status == 'active']

        work_orders_data = [
            {
                'status': 'draft',
                'priority': 'medium',
                'planned_qty': Decimal('100.00'),
                'completed_qty': Decimal('0.00'),
                'scrap_qty': Decimal('0.00'),
                'planned_start': today + timedelta(days=7),
                'planned_end': today + timedelta(days=14),
                'actual_start': None,
                'actual_end': None,
                'notes': 'Draft work order for upcoming production run.',
                'operations': [
                    {'seq': 10, 'name': 'Material Preparation', 'planned_hrs': Decimal('4.00'), 'actual_hrs': Decimal('0.00'), 'status': 'pending'},
                    {'seq': 20, 'name': 'CNC Machining', 'planned_hrs': Decimal('8.00'), 'actual_hrs': Decimal('0.00'), 'status': 'pending'},
                    {'seq': 30, 'name': 'Quality Inspection', 'planned_hrs': Decimal('2.00'), 'actual_hrs': Decimal('0.00'), 'status': 'pending'},
                ],
            },
            {
                'status': 'released',
                'priority': 'high',
                'planned_qty': Decimal('250.00'),
                'completed_qty': Decimal('0.00'),
                'scrap_qty': Decimal('0.00'),
                'planned_start': today + timedelta(days=2),
                'planned_end': today + timedelta(days=9),
                'actual_start': None,
                'actual_end': None,
                'notes': 'Released for production. Materials allocated.',
                'operations': [
                    {'seq': 10, 'name': 'Raw Material Cutting', 'planned_hrs': Decimal('6.00'), 'actual_hrs': Decimal('0.00'), 'status': 'pending'},
                    {'seq': 20, 'name': 'Assembly', 'planned_hrs': Decimal('12.00'), 'actual_hrs': Decimal('0.00'), 'status': 'pending'},
                ],
            },
            {
                'status': 'in_progress',
                'priority': 'high',
                'planned_qty': Decimal('200.00'),
                'completed_qty': Decimal('120.00'),
                'scrap_qty': Decimal('5.00'),
                'planned_start': today - timedelta(days=5),
                'planned_end': today + timedelta(days=3),
                'actual_start': today - timedelta(days=5),
                'actual_end': None,
                'notes': 'Production in progress. 60% complete.',
                'operations': [
                    {'seq': 10, 'name': 'Component Fabrication', 'planned_hrs': Decimal('10.00'), 'actual_hrs': Decimal('11.50'), 'status': 'completed'},
                    {'seq': 20, 'name': 'Sub-Assembly', 'planned_hrs': Decimal('8.00'), 'actual_hrs': Decimal('5.00'), 'status': 'in_progress'},
                    {'seq': 30, 'name': 'Final Assembly', 'planned_hrs': Decimal('6.00'), 'actual_hrs': Decimal('0.00'), 'status': 'pending'},
                ],
            },
            {
                'status': 'on_hold',
                'priority': 'medium',
                'planned_qty': Decimal('150.00'),
                'completed_qty': Decimal('45.00'),
                'scrap_qty': Decimal('3.00'),
                'planned_start': today - timedelta(days=10),
                'planned_end': today - timedelta(days=2),
                'actual_start': today - timedelta(days=10),
                'actual_end': None,
                'notes': 'On hold due to material shortage. Awaiting delivery of component X.',
                'operations': [
                    {'seq': 10, 'name': 'Initial Processing', 'planned_hrs': Decimal('5.00'), 'actual_hrs': Decimal('5.50'), 'status': 'completed'},
                    {'seq': 20, 'name': 'Welding', 'planned_hrs': Decimal('7.00'), 'actual_hrs': Decimal('3.00'), 'status': 'in_progress'},
                ],
            },
            {
                'status': 'completed',
                'priority': 'urgent',
                'planned_qty': Decimal('300.00'),
                'completed_qty': Decimal('295.00'),
                'scrap_qty': Decimal('8.00'),
                'planned_start': today - timedelta(days=20),
                'planned_end': today - timedelta(days=10),
                'actual_start': today - timedelta(days=20),
                'actual_end': today - timedelta(days=9),
                'notes': 'Completed successfully. 98.3% yield rate.',
                'operations': [
                    {'seq': 10, 'name': 'Stamping', 'planned_hrs': Decimal('8.00'), 'actual_hrs': Decimal('7.50'), 'status': 'completed'},
                    {'seq': 20, 'name': 'Surface Treatment', 'planned_hrs': Decimal('6.00'), 'actual_hrs': Decimal('6.25'), 'status': 'completed'},
                    {'seq': 30, 'name': 'Final QC & Packaging', 'planned_hrs': Decimal('4.00'), 'actual_hrs': Decimal('3.75'), 'status': 'completed'},
                ],
            },
            {
                'status': 'cancelled',
                'priority': 'low',
                'planned_qty': Decimal('50.00'),
                'completed_qty': Decimal('0.00'),
                'scrap_qty': Decimal('0.00'),
                'planned_start': today - timedelta(days=15),
                'planned_end': today - timedelta(days=8),
                'actual_start': None,
                'actual_end': None,
                'notes': 'Cancelled due to customer order cancellation.',
                'operations': [
                    {'seq': 10, 'name': 'Preparation', 'planned_hrs': Decimal('3.00'), 'actual_hrs': Decimal('0.00'), 'status': 'skipped'},
                    {'seq': 20, 'name': 'Manufacturing', 'planned_hrs': Decimal('10.00'), 'actual_hrs': Decimal('0.00'), 'status': 'skipped'},
                ],
            },
        ]

        results = []
        for i, data in enumerate(work_orders_data):
            product = product_items[i % len(product_items)]
            user = random.choice(users)
            bom = active_boms[i % len(active_boms)] if active_boms else None
            schedule = schedules[i % len(schedules)] if schedules else None
            wc = work_centers[i % len(work_centers)]

            wo = WorkOrder(
                tenant=tenant,
                product=product,
                bom=bom,
                schedule=schedule,
                work_center=wc,
                status=data['status'],
                planned_quantity=data['planned_qty'],
                completed_quantity=data['completed_qty'],
                scrap_quantity=data['scrap_qty'],
                planned_start_date=data['planned_start'],
                planned_end_date=data['planned_end'],
                actual_start_date=data['actual_start'],
                actual_end_date=data['actual_end'],
                priority=data['priority'],
                notes=data['notes'],
                created_by=user,
            )
            wo.save()

            for op_data in data['operations']:
                op_wc = work_centers[op_data['seq'] // 10 % len(work_centers)]
                WorkOrderOperation.objects.create(
                    work_order=wo,
                    sequence=op_data['seq'],
                    name=op_data['name'],
                    work_center=op_wc,
                    planned_duration_hours=op_data['planned_hrs'],
                    actual_duration_hours=op_data['actual_hrs'],
                    status=op_data['status'],
                    notes=f"{op_data['name']} for {product.name}",
                )
            results.append(wo)
        self.stdout.write(f'  Created {len(results)} work orders with operations')
        return results

    # -------------------------------------------------------------------------
    # MRP RUNS
    # -------------------------------------------------------------------------
    def _create_mrp_runs(self, tenant, users, items, warehouses):
        now = timezone.now()
        today = now.date()
        component_items = items[:min(len(items), 8)]

        # MRP Run 1: Completed with 5 requirements
        mrp1 = MRPRun(
            tenant=tenant,
            title='March 2026 MRP Analysis',
            status='completed',
            run_date=today - timedelta(days=7),
            planning_horizon_days=30,
            notes='Completed MRP run for March planning cycle. All requirements identified.',
            created_by=random.choice(users),
        )
        mrp1.save()

        requirements_data = [
            {'req_qty': Decimal('500.00'), 'on_hand': Decimal('120.00'), 'on_order': Decimal('100.00'), 'notes': 'Critical shortage expected in 2 weeks'},
            {'req_qty': Decimal('300.00'), 'on_hand': Decimal('250.00'), 'on_order': Decimal('0.00'), 'notes': 'Minor shortfall, can expedite existing PO'},
            {'req_qty': Decimal('800.00'), 'on_hand': Decimal('50.00'), 'on_order': Decimal('200.00'), 'notes': 'Large deficit, new purchase order needed'},
            {'req_qty': Decimal('150.00'), 'on_hand': Decimal('200.00'), 'on_order': Decimal('50.00'), 'notes': 'Sufficient stock available, no action needed'},
            {'req_qty': Decimal('400.00'), 'on_hand': Decimal('80.00'), 'on_order': Decimal('150.00'), 'notes': 'Partial coverage, additional order recommended'},
        ]

        for j, req_data in enumerate(requirements_data):
            item = component_items[j % len(component_items)]
            wh = warehouses[j % len(warehouses)]
            net = max(req_data['req_qty'] - req_data['on_hand'] - req_data['on_order'], Decimal('0.00'))
            MRPRequirement.objects.create(
                mrp_run=mrp1,
                item=item,
                warehouse=wh,
                required_quantity=req_data['req_qty'],
                on_hand_quantity=req_data['on_hand'],
                on_order_quantity=req_data['on_order'],
                net_requirement=net,
                planned_order_date=today + timedelta(days=random.randint(3, 14)),
                notes=req_data['notes'],
            )

        # MRP Run 2: Draft
        mrp2 = MRPRun(
            tenant=tenant,
            title='April 2026 MRP Planning',
            status='draft',
            run_date=today,
            planning_horizon_days=45,
            notes='Draft MRP run for April cycle. Awaiting finalized demand forecast.',
            created_by=random.choice(users),
        )
        mrp2.save()

        self.stdout.write(f'  Created 2 MRP runs with requirements')

    # -------------------------------------------------------------------------
    # PRODUCTION LOGS
    # -------------------------------------------------------------------------
    def _create_production_logs(self, tenant, users, work_orders, work_centers):
        now = timezone.now()
        # Get active work orders (in_progress, released, completed)
        active_wos = [wo for wo in work_orders if wo.status in ('in_progress', 'released', 'completed')]
        if not active_wos:
            self.stdout.write(self.style.WARNING('  No active work orders for production logs.'))
            return

        logs_data = [
            {
                'log_type': 'production',
                'start_offset_hrs': -48,
                'duration_hrs': 4,
                'qty_produced': Decimal('45.00'),
                'qty_rejected': Decimal('2.00'),
                'notes': 'Morning shift production run. Steady output.',
            },
            {
                'log_type': 'production',
                'start_offset_hrs': -36,
                'duration_hrs': 6,
                'qty_produced': Decimal('75.00'),
                'qty_rejected': Decimal('3.00'),
                'notes': 'Afternoon shift. Higher throughput after calibration.',
            },
            {
                'log_type': 'setup',
                'start_offset_hrs': -30,
                'duration_hrs': 2,
                'qty_produced': Decimal('0.00'),
                'qty_rejected': Decimal('0.00'),
                'notes': 'Changeover setup for new product batch.',
            },
            {
                'log_type': 'downtime',
                'start_offset_hrs': -24,
                'duration_hrs': 3,
                'qty_produced': Decimal('0.00'),
                'qty_rejected': Decimal('0.00'),
                'notes': 'Unplanned downtime — conveyor belt jam cleared by maintenance.',
            },
            {
                'log_type': 'maintenance',
                'start_offset_hrs': -18,
                'duration_hrs': 2,
                'qty_produced': Decimal('0.00'),
                'qty_rejected': Decimal('0.00'),
                'notes': 'Scheduled preventive maintenance on CNC spindle.',
            },
            {
                'log_type': 'quality_check',
                'start_offset_hrs': -12,
                'duration_hrs': 1,
                'qty_produced': Decimal('0.00'),
                'qty_rejected': Decimal('5.00'),
                'notes': 'Random sample QC check. 5 units failed dimensional tolerance.',
            },
            {
                'log_type': 'production',
                'start_offset_hrs': -8,
                'duration_hrs': 8,
                'qty_produced': Decimal('110.00'),
                'qty_rejected': Decimal('4.00'),
                'notes': 'Full shift production. Night crew achieved target output.',
            },
            {
                'log_type': 'production',
                'start_offset_hrs': -2,
                'duration_hrs': 3,
                'qty_produced': Decimal('35.00'),
                'qty_rejected': Decimal('1.00'),
                'notes': 'Partial shift before scheduled maintenance window.',
            },
        ]

        count = 0
        for i, data in enumerate(logs_data):
            wo = active_wos[i % len(active_wos)]
            wc = work_centers[i % len(work_centers)]
            operator = random.choice(users)
            operations = list(wo.operations.all())
            operation = operations[i % len(operations)] if operations else None

            start_time = now + timedelta(hours=data['start_offset_hrs'])
            end_time = start_time + timedelta(hours=data['duration_hrs'])

            log = ProductionLog(
                tenant=tenant,
                work_order=wo,
                operation=operation,
                work_center=wc,
                operator=operator,
                log_type=data['log_type'],
                start_time=start_time,
                end_time=end_time,
                quantity_produced=data['qty_produced'],
                quantity_rejected=data['qty_rejected'],
                notes=data['notes'],
            )
            log.save()
            count += 1
        self.stdout.write(f'  Created {count} production logs')
