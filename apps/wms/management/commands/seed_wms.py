"""
Management command to seed the database with fake WMS data.

Usage:
    python manage.py seed_wms
    python manage.py seed_wms --flush  (clears WMS data first)

Requires: Tenants, users, procurement items, and inventory warehouses must exist first
          (run seed_data, seed_procurement, and seed_inventory first).
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.inventory.models import Warehouse
from apps.procurement.models import Item
from apps.wms.models import (
    Bin,
    CycleCount,
    CycleCountItem,
    CycleCountPlan,
    DockAppointment,
    PackingOrder,
    PickList,
    PickListItem,
    PutAwayTask,
    ReceivingOrder,
    ReceivingOrderItem,
    ShippingLabel,
    YardLocation,
    YardVisit,
)

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake WMS data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing WMS data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing WMS data...'))
            for model in [
                ShippingLabel, PackingOrder, PickListItem, PickList,
                PutAwayTask, ReceivingOrderItem, ReceivingOrder,
                CycleCountItem, CycleCount, CycleCountPlan,
                YardVisit, YardLocation, DockAppointment, Bin,
            ]:
                model.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('WMS data flushed.'))

        for tenant in tenants:
            # Check if data already exists
            if Bin.objects.filter(tenant=tenant).exists() and not options['flush']:
                self.stdout.write(self.style.WARNING(
                    f'WMS data already exists for tenant "{tenant.name}". Use --flush to re-seed.'
                ))
                continue

            self.stdout.write(f'Seeding WMS data for tenant: {tenant.name}...')

            warehouses = list(Warehouse.objects.filter(tenant=tenant, is_active=True))
            items = list(Item.objects.filter(tenant=tenant, is_active=True))
            users = list(User.objects.filter(tenant=tenant, is_active=True))

            if not warehouses:
                self.stdout.write(self.style.WARNING(
                    f'  No warehouses for tenant "{tenant.name}". Run seed_inventory first.'
                ))
                continue

            if not items:
                self.stdout.write(self.style.WARNING(
                    f'  No items for tenant "{tenant.name}". Run seed_procurement first.'
                ))
                continue

            # 1. Bins
            bins = []
            bin_types = ['bulk', 'pick', 'reserve', 'staging', 'dock']
            zones = ['A', 'B', 'C', 'D']
            for wh in warehouses:
                for i in range(8):
                    zone = random.choice(zones)
                    aisle = str(random.randint(1, 5))
                    rack = str(random.randint(1, 10))
                    shelf = str(random.randint(1, 4))
                    capacity = Decimal(str(random.randint(50, 500)))
                    utilization = Decimal(str(random.randint(0, int(capacity))))
                    b = Bin(
                        tenant=tenant,
                        warehouse=wh,
                        zone=zone,
                        aisle=aisle,
                        rack=rack,
                        shelf=shelf,
                        bin_type=random.choice(bin_types),
                        capacity=capacity,
                        current_utilization=utilization,
                        is_active=True,
                    )
                    b.save()
                    bins.append(b)
            self.stdout.write(f'  Created {len(bins)} bins')

            # 2. Yard Locations
            yard_locations = []
            loc_types = ['dock_door', 'parking_spot', 'staging_area', 'gate']
            for wh in warehouses:
                for i in range(5):
                    yl = YardLocation(
                        tenant=tenant,
                        warehouse=wh,
                        location_type=random.choice(loc_types),
                        is_occupied=random.choice([True, False]),
                        is_active=True,
                        notes=fake.sentence() if random.random() > 0.5 else '',
                    )
                    yl.save()
                    yard_locations.append(yl)
            self.stdout.write(f'  Created {len(yard_locations)} yard locations')

            # 3. Dock Appointments
            dock_appointments = []
            dock_statuses = ['scheduled', 'checked_in', 'receiving', 'completed']
            now = timezone.now()
            for wh in warehouses:
                for i in range(4):
                    days_offset = random.randint(-5, 10)
                    appt_date = (now + timedelta(days=days_offset)).date()
                    status = random.choice(dock_statuses)
                    da = DockAppointment(
                        tenant=tenant,
                        warehouse=wh,
                        dock_number=f'DOCK-{random.randint(1,8)}',
                        appointment_date=appt_date,
                        time_slot=(now + timedelta(hours=random.randint(6, 18))).time(),
                        carrier_name=fake.company(),
                        trailer_number=f'TRL-{random.randint(1000,9999)}',
                        po_reference=f'PO-{random.randint(10000,99999)}' if random.random() > 0.3 else '',
                        status=status,
                        notes=fake.sentence() if random.random() > 0.5 else '',
                    )
                    da.save()
                    dock_appointments.append(da)
            self.stdout.write(f'  Created {len(dock_appointments)} dock appointments')

            # 4. Receiving Orders
            receiving_orders = []
            rcv_statuses = ['pending', 'in_progress', 'completed']
            for da in dock_appointments[:6]:
                ro = ReceivingOrder(
                    tenant=tenant,
                    warehouse=da.warehouse,
                    dock_appointment=da,
                    po_reference=da.po_reference,
                    supplier_name=fake.company(),
                    status=random.choice(rcv_statuses),
                    received_by=random.choice(users) if users else None,
                    notes='',
                )
                ro.save()
                # Add items
                for item in random.sample(items, min(3, len(items))):
                    expected = Decimal(str(random.randint(10, 100)))
                    received = expected if ro.status == 'completed' else Decimal(str(random.randint(0, int(expected))))
                    ReceivingOrderItem.objects.create(
                        receiving_order=ro,
                        item=item,
                        expected_quantity=expected,
                        received_quantity=received,
                        damaged_quantity=Decimal(str(random.randint(0, 3))),
                        bin=random.choice(bins) if random.random() > 0.3 else None,
                    )
                receiving_orders.append(ro)
            self.stdout.write(f'  Created {len(receiving_orders)} receiving orders')

            # 5. Put-Away Tasks
            putaway_tasks = []
            for ro in receiving_orders[:4]:
                for ri in ro.items.all()[:2]:
                    pat = PutAwayTask(
                        tenant=tenant,
                        receiving_order=ro,
                        item=ri.item,
                        quantity=ri.received_quantity,
                        source_bin=random.choice([b for b in bins if b.bin_type == 'staging'] or bins),
                        destination_bin=random.choice([b for b in bins if b.bin_type in ('bulk', 'reserve')] or bins),
                        status=random.choice(['pending', 'in_progress', 'completed']),
                        assigned_to=random.choice(users) if users else None,
                    )
                    pat.save()
                    putaway_tasks.append(pat)
            self.stdout.write(f'  Created {len(putaway_tasks)} put-away tasks')

            # 6. Pick Lists
            pick_lists = []
            pick_types = ['wave', 'batch', 'zone', 'single']
            priorities = ['low', 'medium', 'high', 'urgent']
            for wh in warehouses:
                for i in range(3):
                    pl = PickList(
                        tenant=tenant,
                        warehouse=wh,
                        pick_type=random.choice(pick_types),
                        status=random.choice(['pending', 'in_progress', 'completed']),
                        priority=random.choice(priorities),
                        assigned_to=random.choice(users) if users else None,
                        notes='',
                    )
                    pl.save()
                    # Add items
                    for item in random.sample(items, min(3, len(items))):
                        requested = Decimal(str(random.randint(5, 50)))
                        PickListItem.objects.create(
                            pick_list=pl,
                            item=item,
                            quantity_requested=requested,
                            quantity_picked=requested if pl.status == 'completed' else Decimal('0'),
                            source_bin=random.choice(bins) if random.random() > 0.3 else None,
                            status='picked' if pl.status == 'completed' else 'pending',
                        )
                    pick_lists.append(pl)
            self.stdout.write(f'  Created {len(pick_lists)} pick lists')

            # 7. Packing Orders
            packing_orders = []
            for pl in [p for p in pick_lists if p.status == 'completed'][:4]:
                po = PackingOrder(
                    tenant=tenant,
                    warehouse=pl.warehouse,
                    pick_list=pl,
                    status=random.choice(['pending', 'packing', 'packed', 'shipped']),
                    packer=random.choice(users) if users else None,
                    total_weight=Decimal(str(random.randint(5, 100))),
                    total_packages=random.randint(1, 10),
                    shipping_method=random.choice(['Standard', 'Express', 'Overnight', 'Freight']),
                    tracking_number=f'TRK{random.randint(100000, 999999)}' if random.random() > 0.3 else '',
                )
                po.save()
                packing_orders.append(po)
            self.stdout.write(f'  Created {len(packing_orders)} packing orders')

            # 8. Shipping Labels
            labels_created = 0
            for po in [p for p in packing_orders if p.status in ('packed', 'shipped')]:
                sl = ShippingLabel(
                    tenant=tenant,
                    packing_order=po,
                    carrier=random.choice(['FedEx', 'UPS', 'DHL', 'USPS']),
                    tracking_number=po.tracking_number or f'TRK{random.randint(100000, 999999)}',
                    destination_address=fake.address(),
                    weight=po.total_weight,
                    dimensions=f'{random.randint(10,40)}x{random.randint(10,30)}x{random.randint(5,20)}',
                )
                sl.save()
                labels_created += 1
            self.stdout.write(f'  Created {labels_created} shipping labels')

            # 9. Cycle Count Plans
            plans = []
            for wh in warehouses:
                plan = CycleCountPlan(
                    tenant=tenant,
                    warehouse=wh,
                    name=f'{wh.name} {random.choice(["Monthly", "Weekly", "Quarterly"])} Count',
                    count_type=random.choice(['abc', 'location', 'random', 'full']),
                    frequency=random.choice(['daily', 'weekly', 'monthly', 'quarterly']),
                    status=random.choice(['draft', 'active']),
                    start_date=now.date(),
                    next_count_date=(now + timedelta(days=random.randint(1, 30))).date(),
                )
                plan.save()
                plans.append(plan)
            self.stdout.write(f'  Created {len(plans)} cycle count plans')

            # 10. Cycle Counts
            counts_created = 0
            for plan in plans:
                cc = CycleCount(
                    tenant=tenant,
                    warehouse=plan.warehouse,
                    plan=plan,
                    status=random.choice(['pending', 'in_progress', 'completed']),
                    counter=random.choice(users) if users else None,
                    total_items=0,
                    items_counted=0,
                    variance_count=0,
                )
                cc.save()
                # Add count items
                wh_bins = [b for b in bins if b.warehouse == plan.warehouse]
                count_items = 0
                variance = 0
                for item in random.sample(items, min(4, len(items))):
                    expected = Decimal(str(random.randint(10, 100)))
                    counted = expected + Decimal(str(random.randint(-5, 5)))
                    var = counted - expected
                    CycleCountItem.objects.create(
                        cycle_count=cc,
                        bin=random.choice(wh_bins) if wh_bins else None,
                        item=item,
                        expected_quantity=expected,
                        counted_quantity=counted,
                        variance=var,
                        counted_by=cc.counter,
                        counted_at=now if cc.status == 'completed' else None,
                    )
                    count_items += 1
                    if var != 0:
                        variance += 1
                cc.total_items = count_items
                cc.items_counted = count_items if cc.status == 'completed' else random.randint(0, count_items)
                cc.variance_count = variance
                cc.save()
                counts_created += 1
            self.stdout.write(f'  Created {counts_created} cycle counts')

            # 11. Yard Visits
            visits_created = 0
            visit_statuses = ['expected', 'checked_in', 'at_dock', 'completed', 'departed']
            for yl in yard_locations[:8]:
                yv = YardVisit(
                    tenant=tenant,
                    warehouse=yl.warehouse,
                    yard_location=yl if random.random() > 0.2 else None,
                    carrier_name=fake.company(),
                    driver_name=fake.name(),
                    trailer_number=f'TRL-{random.randint(1000,9999)}',
                    truck_number=f'TRK-{random.randint(100,999)}',
                    visit_type=random.choice(['inbound', 'outbound', 'drop_trailer']),
                    status=random.choice(visit_statuses),
                    appointment=random.choice(dock_appointments) if random.random() > 0.5 else None,
                    check_in_time=now - timedelta(hours=random.randint(1, 48)) if random.random() > 0.3 else None,
                    check_out_time=now if random.random() > 0.6 else None,
                )
                yv.save()
                visits_created += 1
            self.stdout.write(f'  Created {visits_created} yard visits')

            self.stdout.write(self.style.SUCCESS(f'  Done seeding WMS for "{tenant.name}"'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('WMS seed complete!'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Superuser "admin" has no tenant — data won\'t appear when logged in as admin.'
        ))
        self.stdout.write('Log in as a tenant admin (e.g., admin_<tenant-slug>) to see WMS data.')
