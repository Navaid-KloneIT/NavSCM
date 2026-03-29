import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.assets.models import (
    Asset,
    AssetDepreciation,
    AssetSpecification,
    BreakdownMaintenance,
    MaintenanceTask,
    PreventiveMaintenance,
    SparePart,
    SparePartUsage,
)
from apps.core.models import Tenant
from apps.procurement.models import Vendor

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample Asset Management data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete existing assets data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing assets data...')
            SparePartUsage.objects.all().delete()
            SparePart.objects.all().delete()
            AssetDepreciation.objects.all().delete()
            MaintenanceTask.objects.all().delete()
            PreventiveMaintenance.objects.all().delete()
            BreakdownMaintenance.objects.all().delete()
            AssetSpecification.objects.all().delete()
            Asset.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Flushed.'))

        today = timezone.now().date()

        for tenant in tenants:
            self.stdout.write(f'\nSeeding assets data for tenant: {tenant.name}')

            users = list(User.objects.filter(tenant=tenant, is_active=True)[:5])
            vendors = list(Vendor.objects.filter(tenant=tenant, is_active=True)[:5])

            if not users:
                self.stdout.write(self.style.WARNING(f'  No users for {tenant.name}. Skipping.'))
                continue

            if Asset.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    f'  Data already exists for {tenant.name}. Use --flush to re-seed.'
                ))
                continue

            # -----------------------------------------------------------------
            # 1. Asset Registry
            # -----------------------------------------------------------------
            asset_data = [
                ('Delivery Truck #1', 'truck', 'Volvo', 'FH16', 85000),
                ('Delivery Truck #2', 'truck', 'MAN', 'TGX', 78000),
                ('Warehouse Forklift A', 'forklift', 'Toyota', '8FBN25', 35000),
                ('Warehouse Forklift B', 'forklift', 'Hyster', 'H50FT', 32000),
                ('Packaging Machine', 'machinery', 'Bosch', 'PKG-200', 120000),
                ('Conveyor Belt System', 'conveyor', 'Hytrol', 'EZ-Logic', 95000),
                ('Fleet Van #1', 'vehicle', 'Ford', 'Transit', 42000),
                ('CNC Milling Machine', 'machinery', 'Haas', 'VF-2', 150000),
                ('Office Server Rack', 'computer', 'Dell', 'PowerEdge R740', 18000),
                ('Cold Storage Unit', 'equipment', 'Carrier', 'CS-500', 65000),
            ]
            asset_statuses = ['draft', 'active', 'active', 'active', 'active', 'in_maintenance', 'active', 'active', 'out_of_service', 'active']
            conditions = ['new', 'good', 'good', 'fair', 'good', 'fair', 'good', 'new', 'poor', 'good']
            locations = ['Warehouse A', 'Warehouse B', 'Loading Dock', 'Production Floor', 'Office Building', 'Cold Storage']
            assets_created = []

            for i, (name, atype, mfr, model, cost) in enumerate(asset_data):
                a = Asset(
                    tenant=tenant,
                    name=name,
                    asset_type=atype,
                    status=asset_statuses[i],
                    condition=conditions[i],
                    manufacturer=mfr,
                    model_number=model,
                    serial_number=f'SN-{random.randint(100000, 999999)}',
                    purchase_date=today - timedelta(days=random.randint(90, 1800)),
                    purchase_cost=cost,
                    currency='USD',
                    warranty_expiry=today + timedelta(days=random.randint(-180, 730)),
                    location=random.choice(locations),
                    assigned_to=random.choice(users),
                    description=f'{name} used in supply chain operations.',
                    created_by=random.choice(users),
                )
                a.save()
                assets_created.append(a)

                # Specs
                spec_templates = [
                    ('Weight', f'{random.randint(500, 15000)}', 'kg'),
                    ('Max Load', f'{random.randint(1000, 30000)}', 'kg'),
                    ('Power', f'{random.randint(50, 500)}', 'HP'),
                    ('Fuel Type', random.choice(['Diesel', 'Electric', 'Gasoline', 'N/A']), ''),
                ]
                for s_name, s_val, s_unit in random.sample(spec_templates, random.randint(2, 3)):
                    AssetSpecification.objects.create(
                        asset=a, spec_name=s_name, spec_value=s_val, unit=s_unit,
                    )

            self.stdout.write(f'  Created {len(assets_created)} assets with specifications.')

            # -----------------------------------------------------------------
            # 2. Preventive Maintenance
            # -----------------------------------------------------------------
            pm_titles = [
                'Oil Change & Filter Replacement',
                'Hydraulic System Inspection',
                'Electrical System Check',
                'Safety Equipment Inspection',
                'Belt & Chain Lubrication',
                'Coolant System Flush',
                'Brake System Inspection',
                'Annual Calibration',
            ]
            pm_statuses = ['draft', 'scheduled', 'scheduled', 'in_progress', 'completed', 'completed', 'overdue', 'cancelled']
            frequencies = ['weekly', 'monthly', 'monthly', 'quarterly', 'quarterly', 'semi_annual', 'annual', 'annual']
            priorities = ['low', 'medium', 'medium', 'high', 'medium', 'low', 'urgent', 'medium']
            pms_created = []

            for i, title in enumerate(pm_titles):
                asset = assets_created[i % len(assets_created)]
                pm = PreventiveMaintenance(
                    tenant=tenant,
                    asset=asset,
                    title=title,
                    frequency=frequencies[i],
                    priority=priorities[i],
                    status=pm_statuses[i],
                    scheduled_date=today + timedelta(days=random.randint(-30, 60)),
                    next_due_date=today + timedelta(days=random.randint(14, 180)),
                    estimated_duration_hours=Decimal(str(round(random.uniform(1, 8), 2))),
                    actual_duration_hours=Decimal(str(round(random.uniform(1, 10), 2))) if pm_statuses[i] == 'completed' else Decimal('0'),
                    estimated_cost=random.randint(100, 5000),
                    actual_cost=random.randint(100, 6000) if pm_statuses[i] == 'completed' else 0,
                    completed_date=today - timedelta(days=random.randint(1, 30)) if pm_statuses[i] == 'completed' else None,
                    assigned_to=random.choice(users),
                    description=f'{title} for {asset.name}.',
                    created_by=random.choice(users),
                )
                pm.save()
                pms_created.append(pm)

                # Tasks
                task_names = ['Inspect components', 'Replace worn parts', 'Test operation', 'Document findings', 'Clean area']
                for t_name in random.sample(task_names, random.randint(2, 4)):
                    MaintenanceTask.objects.create(
                        maintenance=pm,
                        task_name=t_name,
                        status=random.choice(['pending', 'completed', 'in_progress']) if pm.status != 'draft' else 'pending',
                    )

            self.stdout.write(f'  Created {len(pms_created)} preventive maintenance schedules with tasks.')

            # -----------------------------------------------------------------
            # 3. Breakdown Maintenance
            # -----------------------------------------------------------------
            bm_titles = [
                'Engine overheating',
                'Hydraulic leak detected',
                'Electrical failure',
                'Conveyor belt snapped',
                'Forklift steering malfunction',
                'Compressor failure',
            ]
            bm_statuses = ['reported', 'assigned', 'diagnosing', 'repairing', 'completed', 'closed']
            severities = ['minor', 'moderate', 'major', 'critical', 'moderate', 'minor']
            bms_created = []

            for i, title in enumerate(bm_titles):
                asset = assets_created[i % len(assets_created)]
                reported = timezone.now() - timedelta(days=random.randint(1, 30))
                bm = BreakdownMaintenance(
                    tenant=tenant,
                    asset=asset,
                    title=title,
                    severity=severities[i],
                    status=bm_statuses[i],
                    reported_date=reported,
                    started_date=reported + timedelta(hours=random.randint(1, 24)) if bm_statuses[i] not in ('reported',) else None,
                    completed_date=reported + timedelta(days=random.randint(1, 7)) if bm_statuses[i] in ('completed', 'closed') else None,
                    downtime_hours=Decimal(str(round(random.uniform(2, 72), 2))),
                    repair_cost=random.randint(200, 15000),
                    root_cause='Wear and tear from extended use.' if i % 2 == 0 else 'Component failure due to material defect.',
                    repair_description='Replaced faulty component and tested operation.' if bm_statuses[i] in ('completed', 'closed') else '',
                    assigned_to=random.choice(users),
                    reported_by=random.choice(users),
                )
                bm.save()
                bms_created.append(bm)

            self.stdout.write(f'  Created {len(bms_created)} breakdown maintenance records.')

            # -----------------------------------------------------------------
            # 4. Spare Parts Inventory
            # -----------------------------------------------------------------
            part_data = [
                ('Hydraulic Filter', 'Filters', 25, 5, 45.00),
                ('Drive Belt', 'Belts', 15, 3, 120.00),
                ('Brake Pad Set', 'Braking', 20, 5, 85.00),
                ('Oil Filter', 'Filters', 50, 10, 25.00),
                ('Forklift Battery', 'Electrical', 3, 1, 1200.00),
                ('Conveyor Roller', 'Conveyor Parts', 12, 4, 250.00),
                ('Coolant Hose', 'Hoses', 8, 3, 65.00),
                ('Electric Motor Bearing', 'Bearings', 30, 8, 35.00),
            ]
            part_statuses = ['in_stock', 'in_stock', 'in_stock', 'in_stock', 'low_stock', 'in_stock', 'low_stock', 'in_stock']
            parts_created = []

            for i, (name, cat, qty, reorder, cost) in enumerate(part_data):
                sp = SparePart(
                    tenant=tenant,
                    name=name,
                    description=f'{name} for maintenance operations.',
                    category=cat,
                    quantity_on_hand=qty,
                    reorder_level=reorder,
                    reorder_quantity=reorder * 2,
                    unit_cost=Decimal(str(cost)),
                    currency='USD',
                    status=part_statuses[i],
                    location=random.choice(['Parts Room A', 'Parts Room B', 'Main Warehouse']),
                    vendor=random.choice(vendors) if vendors else None,
                    created_by=random.choice(users),
                )
                sp.save()
                parts_created.append(sp)

                # Usage records
                for _ in range(random.randint(1, 3)):
                    SparePartUsage.objects.create(
                        spare_part=sp,
                        asset=random.choice(assets_created),
                        breakdown=random.choice(bms_created) if bms_created else None,
                        quantity_used=random.randint(1, 3),
                        used_date=today - timedelta(days=random.randint(1, 90)),
                        notes='Routine replacement' if random.random() > 0.5 else '',
                    )

            self.stdout.write(f'  Created {len(parts_created)} spare parts with usage records.')

            # -----------------------------------------------------------------
            # 5. Asset Depreciation
            # -----------------------------------------------------------------
            dep_statuses = ['draft', 'active', 'active', 'active', 'active', 'fully_depreciated', 'active']
            methods = ['straight_line', 'straight_line', 'declining_balance', 'straight_line', 'double_declining', 'straight_line', 'straight_line']
            deps_created = []

            for i in range(min(7, len(assets_created))):
                asset = assets_created[i]
                original = float(asset.purchase_cost)
                salvage = round(original * random.uniform(0.05, 0.15), 2)
                useful_life = random.choice([3, 5, 7, 10])
                annual = round((original - salvage) / useful_life, 2)
                years_elapsed = random.randint(0, useful_life)
                accumulated = min(round(annual * years_elapsed, 2), original - salvage)
                book_value = round(original - accumulated, 2)

                dep = AssetDepreciation(
                    tenant=tenant,
                    asset=asset,
                    method=methods[i],
                    status=dep_statuses[i],
                    original_cost=Decimal(str(original)),
                    salvage_value=Decimal(str(salvage)),
                    useful_life_years=useful_life,
                    start_date=asset.purchase_date,
                    annual_depreciation=Decimal(str(annual)),
                    accumulated_depreciation=Decimal(str(accumulated)),
                    current_book_value=Decimal(str(book_value)),
                    currency=asset.currency,
                    notes=f'Depreciation schedule for {asset.name}.',
                    created_by=random.choice(users),
                )
                dep.save()
                deps_created.append(dep)

            self.stdout.write(f'  Created {len(deps_created)} asset depreciation records.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Asset Management data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Superuser "admin" has no tenant — '
            'data won\'t appear when logged in as admin. '
            'Use a tenant admin account (e.g., admin_<slug>) to see the data.'
        ))
