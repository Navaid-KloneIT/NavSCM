"""
Management command to seed the database with fake inventory data.

Usage:
    python manage.py seed_inventory
    python manage.py seed_inventory --flush  (clears inventory data first)

Requires: Tenants, users, and procurement items must exist first
          (run seed_data and seed_procurement first).
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.procurement.models import Item
from apps.inventory.models import (
    InventoryValuation,
    InventoryValuationItem,
    ReorderRule,
    ReorderSuggestion,
    StockAdjustment,
    StockAdjustmentItem,
    StockItem,
    Warehouse,
    WarehouseLocation,
    WarehouseTransfer,
    WarehouseTransferItem,
)

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake inventory data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing inventory data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing inventory data...'))
            InventoryValuationItem.objects.all().delete()
            InventoryValuation.objects.all().delete()
            ReorderSuggestion.objects.all().delete()
            ReorderRule.objects.all().delete()
            StockAdjustmentItem.objects.all().delete()
            StockAdjustment.objects.all().delete()
            WarehouseTransferItem.objects.all().delete()
            WarehouseTransfer.objects.all().delete()
            StockItem.objects.all().delete()
            WarehouseLocation.objects.all().delete()
            Warehouse.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All inventory data flushed.'))

        tenant_admins = []

        for tenant in tenants:
            self.stdout.write(f'\nSeeding inventory data for: {tenant.name}')
            users = list(User.objects.filter(tenant=tenant, is_active=True))

            if not users:
                self.stdout.write(self.style.WARNING(f'  No users found, skipping.'))
                continue

            # Check if procurement items exist
            items = list(Item.objects.filter(tenant=tenant, is_active=True))
            if not items:
                self.stdout.write(self.style.WARNING(
                    f'  No procurement items found. Run "python manage.py seed_procurement" first.'
                ))
                continue

            # Check if inventory data already exists for this tenant
            if Warehouse.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    f'  Inventory data already exists. Use --flush to re-seed.'
                ))
                continue

            # Find tenant admin for login info
            admin_user = User.objects.filter(
                tenant=tenant, is_tenant_admin=True
            ).first()
            if admin_user:
                tenant_admins.append(admin_user.username)

            warehouses = self._create_warehouses(tenant)
            locations = self._create_locations(tenant, warehouses)
            stock_items = self._create_stock_items(tenant, items, warehouses, locations)
            self._create_warehouse_transfers(tenant, users, items, warehouses)
            self._create_stock_adjustments(tenant, users, items, warehouses, stock_items)
            reorder_rules = self._create_reorder_rules(tenant, items, warehouses)
            self._create_reorder_suggestions(tenant, reorder_rules, stock_items)
            self._create_inventory_valuations(tenant, users, items, warehouses, stock_items)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Inventory seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('To see inventory data, log in as a tenant admin:')
        for username in tenant_admins:
            self.stdout.write(f'  Username: {username} / Password: password123')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: The superuser "admin" has no tenant, so inventory data '
            'will NOT appear when logged in as admin.'
        ))

    def _create_warehouses(self, tenant):
        warehouse_data = [
            ('Main Distribution Center', 'WH-00001', 'main', '123 Industrial Blvd', 'New York', 'United States'),
            ('East Branch Warehouse', 'WH-00002', 'branch', '456 Commerce Ave', 'Boston', 'United States'),
            ('West Branch Warehouse', 'WH-00003', 'branch', '789 Logistics Park', 'Los Angeles', 'United States'),
            ('South Storage Facility', 'WH-00004', 'branch', '321 Warehouse Lane', 'Houston', 'United States'),
            ('Transit Hub Central', 'WH-00005', 'transit', '555 Transit Road', 'Chicago', 'United States'),
        ]

        warehouses = []
        for name, code, wh_type, address, city, country in warehouse_data:
            wh, _ = Warehouse.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    'name': name,
                    'warehouse_type': wh_type,
                    'address': address,
                    'city': city,
                    'country': country,
                    'is_active': True,
                },
            )
            warehouses.append(wh)

        self.stdout.write(f'  Created {len(warehouses)} warehouses')
        return warehouses

    def _create_locations(self, tenant, warehouses):
        # Location templates per zone
        zone_locations = {
            'receiving': [
                ('Receiving Dock A', 'RCV-A'),
                ('Receiving Dock B', 'RCV-B'),
            ],
            'storage': [
                ('Aisle 1 - Rack A', 'STR-1A'),
                ('Aisle 1 - Rack B', 'STR-1B'),
                ('Aisle 2 - Rack A', 'STR-2A'),
                ('Aisle 2 - Rack B', 'STR-2B'),
                ('Aisle 3 - Rack A', 'STR-3A'),
                ('Bulk Storage Area', 'STR-BLK'),
            ],
            'picking': [
                ('Pick Zone 1', 'PCK-01'),
                ('Pick Zone 2', 'PCK-02'),
            ],
            'shipping': [
                ('Shipping Dock 1', 'SHP-01'),
                ('Shipping Dock 2', 'SHP-02'),
            ],
        }

        locations = []
        for warehouse in warehouses:
            for zone, locs in zone_locations.items():
                for name, code in locs:
                    loc, _ = WarehouseLocation.objects.get_or_create(
                        tenant=tenant,
                        warehouse=warehouse,
                        code=code,
                        defaults={
                            'name': name,
                            'zone': zone,
                            'is_active': True,
                        },
                    )
                    locations.append(loc)

        self.stdout.write(f'  Created {len(locations)} warehouse locations')
        return locations

    def _create_stock_items(self, tenant, items, warehouses, locations):
        stock_items = []
        main_warehouse = warehouses[0]  # Main Distribution Center
        branch_warehouses = warehouses[1:4]  # Branch warehouses

        # Stock most items in the main warehouse
        for item in items:
            storage_locs = [l for l in locations if l.warehouse == main_warehouse and l.zone == 'storage']
            location = random.choice(storage_locs) if storage_locs else None

            qty_on_hand = Decimal(str(random.randint(20, 500)))
            qty_reserved = Decimal(str(random.randint(0, int(qty_on_hand * Decimal('0.3')))))
            reorder_pt = Decimal(str(random.randint(10, 50)))
            reorder_qty = Decimal(str(random.randint(50, 200)))
            safety = Decimal(str(random.randint(5, 20)))

            si, _ = StockItem.objects.get_or_create(
                tenant=tenant,
                item=item,
                warehouse=main_warehouse,
                batch_number='',
                defaults={
                    'location': location,
                    'quantity_on_hand': qty_on_hand,
                    'quantity_reserved': qty_reserved,
                    'reorder_point': reorder_pt,
                    'reorder_quantity': reorder_qty,
                    'safety_stock': safety,
                    'unit_cost': item.unit_price,
                    'last_received_date': timezone.now() - timedelta(days=random.randint(1, 30)),
                    'last_issued_date': timezone.now() - timedelta(days=random.randint(0, 15)),
                },
            )
            stock_items.append(si)

        # Stock a subset of items in branch warehouses
        for warehouse in branch_warehouses:
            selected_items = random.sample(items, k=min(len(items), random.randint(10, 20)))
            for item in selected_items:
                storage_locs = [l for l in locations if l.warehouse == warehouse and l.zone == 'storage']
                location = random.choice(storage_locs) if storage_locs else None

                qty_on_hand = Decimal(str(random.randint(5, 150)))
                qty_reserved = Decimal(str(random.randint(0, int(qty_on_hand * Decimal('0.2')))))

                si, _ = StockItem.objects.get_or_create(
                    tenant=tenant,
                    item=item,
                    warehouse=warehouse,
                    batch_number='',
                    defaults={
                        'location': location,
                        'quantity_on_hand': qty_on_hand,
                        'quantity_reserved': qty_reserved,
                        'reorder_point': Decimal(str(random.randint(5, 20))),
                        'reorder_quantity': Decimal(str(random.randint(20, 100))),
                        'safety_stock': Decimal(str(random.randint(3, 10))),
                        'unit_cost': item.unit_price,
                        'last_received_date': timezone.now() - timedelta(days=random.randint(1, 45)),
                    },
                )
                stock_items.append(si)

        # Add some batch-tracked items (raw materials with batch numbers)
        raw_materials = [i for i in items if i.code.startswith('RAW')]
        for item in raw_materials:
            for batch_idx in range(random.randint(1, 3)):
                batch_num = f'BATCH-{item.code}-{batch_idx + 1:03d}'
                si, _ = StockItem.objects.get_or_create(
                    tenant=tenant,
                    item=item,
                    warehouse=main_warehouse,
                    batch_number=batch_num,
                    defaults={
                        'quantity_on_hand': Decimal(str(random.randint(50, 300))),
                        'unit_cost': item.unit_price * Decimal(str(random.uniform(0.9, 1.1))).quantize(Decimal('0.01')),
                        'expiry_date': (timezone.now() + timedelta(days=random.randint(90, 365))).date(),
                        'last_received_date': timezone.now() - timedelta(days=random.randint(5, 60)),
                    },
                )
                stock_items.append(si)

        self.stdout.write(f'  Created {len(stock_items)} stock items')
        return stock_items

    def _create_warehouse_transfers(self, tenant, users, items, warehouses):
        if len(warehouses) < 2:
            return

        statuses = ['draft', 'pending', 'in_transit', 'in_transit', 'received', 'received', 'cancelled']
        transfers = []

        for i in range(10):
            trf_number = f'TRF-{i + 1:05d}'

            existing = WarehouseTransfer.objects.filter(
                tenant=tenant, transfer_number=trf_number
            ).first()
            if existing:
                transfers.append(existing)
                continue

            source = random.choice(warehouses)
            dest = random.choice([w for w in warehouses if w != source])
            status = random.choice(statuses)

            trf = WarehouseTransfer(
                tenant=tenant,
                transfer_number=trf_number,
                source_warehouse=source,
                destination_warehouse=dest,
                status=status,
                requested_by=random.choice(users),
                transfer_date=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )

            if status in ('in_transit', 'received'):
                trf.approved_by = random.choice(users)
            if status == 'received':
                trf.received_date = timezone.now().date() - timedelta(days=random.randint(0, 5))

            trf.save()

            # Add 2-4 transfer line items
            selected_items = random.sample(items, k=random.randint(2, 4))
            for item in selected_items:
                qty_requested = Decimal(str(random.randint(5, 50)))
                qty_sent = qty_requested if status in ('in_transit', 'received') else Decimal('0')
                qty_received = qty_requested if status == 'received' else Decimal('0')

                WarehouseTransferItem.objects.create(
                    transfer=trf,
                    item=item,
                    quantity_requested=qty_requested,
                    quantity_sent=qty_sent,
                    quantity_received=qty_received,
                    notes=fake.sentence() if random.random() > 0.7 else '',
                )

            transfers.append(trf)

        self.stdout.write(f'  Created {len(transfers)} warehouse transfers')

    def _create_stock_adjustments(self, tenant, users, items, warehouses, stock_items):
        adj_types = ['write_off', 'damage', 'cycle_count', 'correction', 'return']
        statuses = ['draft', 'pending', 'approved', 'approved', 'approved', 'rejected']
        reasons = [
            'Cycle count discrepancy found during quarterly audit',
            'Items damaged during forklift operation',
            'Expired stock write-off per policy',
            'Correction after physical inventory count',
            'Customer return - items in good condition',
            'Water damage in storage area B',
            'Quantity mismatch identified in system reconciliation',
            'Defective batch returned by production',
        ]

        adjustments = []
        for i in range(8):
            adj_number = f'ADJ-{i + 1:05d}'

            existing = StockAdjustment.objects.filter(
                tenant=tenant, adjustment_number=adj_number
            ).first()
            if existing:
                adjustments.append(existing)
                continue

            warehouse = random.choice(warehouses[:4])  # Exclude transit hub
            status = random.choice(statuses)
            adj_type = random.choice(adj_types)

            adj = StockAdjustment(
                tenant=tenant,
                adjustment_number=adj_number,
                warehouse=warehouse,
                adjustment_type=adj_type,
                status=status,
                reason=random.choice(reasons),
                adjusted_by=random.choice(users),
                adjustment_date=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            if status in ('approved', 'rejected'):
                adj.approved_by = random.choice(users)
            adj.save()

            # Add 1-4 adjustment line items
            wh_stock = [si for si in stock_items if si.warehouse == warehouse]
            if not wh_stock:
                wh_stock = stock_items[:5]

            selected_stock = random.sample(wh_stock, k=min(len(wh_stock), random.randint(1, 4)))
            for si in selected_stock:
                qty_before = si.quantity_on_hand
                if adj_type in ('write_off', 'damage'):
                    qty_adj = -Decimal(str(random.randint(1, max(1, int(qty_before * Decimal('0.2'))))))
                elif adj_type == 'return':
                    qty_adj = Decimal(str(random.randint(1, 20)))
                else:
                    qty_adj = Decimal(str(random.randint(-10, 10)))

                StockAdjustmentItem.objects.create(
                    adjustment=adj,
                    item=si.item,
                    stock_item=si,
                    quantity_before=qty_before,
                    quantity_adjustment=qty_adj,
                    quantity_after=qty_before + qty_adj,
                    unit_cost=si.unit_cost,
                    notes=fake.sentence() if random.random() > 0.6 else '',
                )

            adjustments.append(adj)

        self.stdout.write(f'  Created {len(adjustments)} stock adjustments')

    def _create_reorder_rules(self, tenant, items, warehouses):
        main_warehouse = warehouses[0]
        rules = []

        # Create reorder rules for ~60% of items in main warehouse
        selected_items = random.sample(items, k=int(len(items) * 0.6))
        for item in selected_items:
            reorder_pt = Decimal(str(random.randint(10, 50)))
            rule, _ = ReorderRule.objects.get_or_create(
                tenant=tenant,
                item=item,
                warehouse=main_warehouse,
                defaults={
                    'reorder_point': reorder_pt,
                    'reorder_quantity': Decimal(str(random.randint(50, 200))),
                    'safety_stock': Decimal(str(random.randint(5, int(reorder_pt)))),
                    'lead_time_days': random.randint(3, 21),
                    'is_active': True,
                    'last_triggered_at': timezone.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.4 else None,
                },
            )
            rules.append(rule)

        self.stdout.write(f'  Created {len(rules)} reorder rules')
        return rules

    def _create_reorder_suggestions(self, tenant, reorder_rules, stock_items):
        statuses = ['pending', 'pending', 'approved', 'dismissed', 'po_created']
        suggestions = []

        # Generate suggestions for ~40% of rules
        selected_rules = random.sample(reorder_rules, k=max(1, int(len(reorder_rules) * 0.4)))
        for rule in selected_rules:
            # Find matching stock item
            matching_stock = [
                si for si in stock_items
                if si.item == rule.item and si.warehouse == rule.warehouse and si.batch_number == ''
            ]
            current_stock = matching_stock[0].quantity_on_hand if matching_stock else Decimal('0')

            suggestion = ReorderSuggestion.objects.create(
                tenant=tenant,
                rule=rule,
                item=rule.item,
                warehouse=rule.warehouse,
                suggested_quantity=rule.reorder_quantity,
                current_stock=current_stock,
                reorder_point=rule.reorder_point,
                status=random.choice(statuses),
            )
            suggestions.append(suggestion)

        self.stdout.write(f'  Created {len(suggestions)} reorder suggestions')

    def _create_inventory_valuations(self, tenant, users, items, warehouses, stock_items):
        methods = ['fifo', 'lifo', 'weighted_avg']
        main_warehouse = warehouses[0]

        valuations = []
        for i in range(4):
            val_number = f'VAL-{i + 1:05d}'

            existing = InventoryValuation.objects.filter(
                tenant=tenant, valuation_number=val_number
            ).first()
            if existing:
                valuations.append(existing)
                continue

            method = methods[i % len(methods)]
            is_completed = random.random() > 0.3
            warehouse = main_warehouse if i < 2 else random.choice(warehouses[:4])

            # Calculate totals from stock
            wh_stock = [si for si in stock_items if si.warehouse == warehouse and si.batch_number == '']
            total_value = sum(si.quantity_on_hand * si.unit_cost for si in wh_stock)

            val = InventoryValuation(
                tenant=tenant,
                valuation_number=val_number,
                warehouse=warehouse if i > 0 else None,  # First one = all warehouses
                valuation_method=method,
                valuation_date=timezone.now().date() - timedelta(days=i * 7),
                total_value=total_value.quantize(Decimal('0.01')) if total_value else Decimal('0'),
                total_items=len(wh_stock),
                status='completed' if is_completed else 'draft',
                created_by=random.choice(users),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            val.save()

            # Add valuation line items
            target_stock = wh_stock if warehouse else stock_items
            for si in target_stock[:15]:  # Limit to 15 items per valuation
                if si.batch_number:
                    continue
                InventoryValuationItem.objects.create(
                    valuation=val,
                    item=si.item,
                    warehouse=si.warehouse,
                    quantity_on_hand=si.quantity_on_hand,
                    unit_cost=si.unit_cost,
                    total_value=(si.quantity_on_hand * si.unit_cost).quantize(Decimal('0.01')),
                    valuation_method=method,
                )

            valuations.append(val)

        self.stdout.write(f'  Created {len(valuations)} inventory valuations')
