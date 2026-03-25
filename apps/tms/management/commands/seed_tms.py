import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.procurement.models import Item
from apps.tms.models import (
    Carrier,
    FreightBill,
    FreightBillItem,
    LoadPlan,
    LoadPlanItem,
    RateCard,
    Route,
    Shipment,
    ShipmentItem,
    ShipmentTracking,
)

from faker import Faker

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake TMS data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing TMS data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing TMS data...'))
            LoadPlanItem.objects.all().delete()
            LoadPlan.objects.all().delete()
            FreightBillItem.objects.all().delete()
            FreightBill.objects.all().delete()
            ShipmentTracking.objects.all().delete()
            ShipmentItem.objects.all().delete()
            Shipment.objects.all().delete()
            Route.objects.all().delete()
            RateCard.objects.all().delete()
            Carrier.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All TMS data flushed.'))

        for tenant in tenants:
            if Carrier.objects.filter(tenant=tenant).exists() and not options['flush']:
                self.stdout.write(self.style.WARNING(
                    f'TMS data already exists for tenant "{tenant.name}". Use --flush to re-seed.'
                ))
                continue

            self.stdout.write(f'Seeding TMS data for tenant: {tenant.name}...')

            users = list(User.objects.filter(tenant=tenant))
            items = list(Item.objects.filter(tenant=tenant, is_active=True))

            if not users:
                self.stdout.write(self.style.WARNING(
                    f'  No users for tenant "{tenant.name}". Skipping.'
                ))
                continue

            # -----------------------------------------------------------------
            # CARRIERS
            # -----------------------------------------------------------------
            carrier_data = [
                ('FastFreight Logistics', 'ftl', 'John Miller'),
                ('AirCargo Express', 'air_freight', 'Sarah Chen'),
                ('OceanWay Shipping', 'ocean_freight', 'Ahmed Hassan'),
                ('QuickParcel Co.', 'parcel', 'Maria Garcia'),
                ('RailLink Transport', 'rail', 'David Kim'),
                ('CityRunner Courier', 'courier', 'Lisa Brown'),
                ('HeavyHaul Trucking', 'ltl', 'Robert Wilson'),
            ]

            carriers = []
            for name, ctype, contact in carrier_data:
                carrier = Carrier(
                    tenant=tenant,
                    name=name,
                    contact_person=contact,
                    email=fake.company_email(),
                    phone=fake.phone_number()[:20],
                    address=fake.address(),
                    carrier_type=ctype,
                    rating=Decimal(str(round(random.uniform(3.0, 5.0), 1))),
                    is_active=True,
                )
                carrier.save()
                carriers.append(carrier)
            self.stdout.write(f'  Created {len(carriers)} carriers.')

            # -----------------------------------------------------------------
            # RATE CARDS
            # -----------------------------------------------------------------
            routes_data = [
                ('New York', 'Los Angeles'),
                ('Chicago', 'Houston'),
                ('London', 'Frankfurt'),
                ('Shanghai', 'Singapore'),
                ('Dubai', 'Karachi'),
            ]
            modes = ['road', 'air', 'ocean', 'rail', 'multimodal']
            currencies = ['USD', 'EUR', 'GBP', 'PKR']
            unit_types = ['per_kg', 'per_cbm', 'per_pallet', 'per_container', 'flat_rate']

            rate_cards = []
            for origin, dest in routes_data:
                carrier = random.choice(carriers)
                rate = RateCard(
                    tenant=tenant,
                    carrier=carrier,
                    origin=origin,
                    destination=dest,
                    transport_mode=random.choice(modes),
                    rate_per_unit=Decimal(str(round(random.uniform(5.0, 500.0), 2))),
                    currency=random.choice(currencies),
                    unit_type=random.choice(unit_types),
                    min_charge=Decimal(str(round(random.uniform(50.0, 500.0), 2))),
                    max_weight=Decimal(str(round(random.uniform(1000.0, 50000.0), 2))),
                    transit_days=random.randint(1, 30),
                    effective_from=timezone.now().date() - timedelta(days=random.randint(30, 90)),
                    effective_to=timezone.now().date() + timedelta(days=random.randint(90, 365)),
                    is_active=True,
                )
                rate.save()
                rate_cards.append(rate)
            self.stdout.write(f'  Created {len(rate_cards)} rate cards.')

            # -----------------------------------------------------------------
            # ROUTES
            # -----------------------------------------------------------------
            route_names = [
                ('East Coast Express', 'New York', 'Miami', 2000, 24),
                ('Cross Country', 'Los Angeles', 'Chicago', 3200, 36),
                ('Northeast Corridor', 'Boston', 'Washington DC', 700, 8),
                ('Southern Route', 'Dallas', 'Atlanta', 1200, 14),
                ('Pacific Highway', 'Seattle', 'San Francisco', 1300, 16),
            ]
            statuses = ['draft', 'active', 'active', 'active', 'inactive']

            route_objs = []
            for i, (name, origin, dest, dist, hours) in enumerate(route_names):
                route = Route(
                    tenant=tenant,
                    name=name,
                    origin=origin,
                    destination=dest,
                    distance_km=Decimal(str(dist)),
                    estimated_time_hours=Decimal(str(hours)),
                    carrier=random.choice(carriers),
                    transport_mode='road',
                    waypoints=', '.join([fake.city() for _ in range(random.randint(1, 3))]),
                    status=statuses[i],
                    fuel_cost_estimate=Decimal(str(round(dist * 0.15, 2))),
                    toll_cost_estimate=Decimal(str(round(random.uniform(20.0, 200.0), 2))),
                )
                route.save()
                route_objs.append(route)
            self.stdout.write(f'  Created {len(route_objs)} routes.')

            # -----------------------------------------------------------------
            # SHIPMENTS
            # -----------------------------------------------------------------
            shipment_statuses = [
                'draft', 'booked', 'picked_up', 'in_transit',
                'in_transit', 'delivered', 'delivered', 'delivered',
            ]
            priorities = ['low', 'medium', 'medium', 'high', 'urgent']

            shipments = []
            for i in range(8):
                status = shipment_statuses[i]
                carrier = random.choice(carriers)
                route = random.choice(route_objs)
                now = timezone.now()

                shipment = Shipment(
                    tenant=tenant,
                    carrier=carrier,
                    route=route,
                    origin_address=fake.address(),
                    destination_address=fake.address(),
                    status=status,
                    priority=random.choice(priorities),
                    transport_mode=random.choice(modes),
                    estimated_departure=now - timedelta(days=random.randint(1, 10)),
                    estimated_arrival=now + timedelta(days=random.randint(1, 15)),
                    total_weight=Decimal(str(round(random.uniform(100.0, 10000.0), 2))),
                    total_volume=Decimal(str(round(random.uniform(5.0, 500.0), 2))),
                    current_location=fake.city() if status in ('in_transit', 'at_hub', 'out_for_delivery') else '',
                    shipped_by=random.choice(users),
                )
                if status in ('picked_up', 'in_transit', 'delivered'):
                    shipment.actual_departure = now - timedelta(days=random.randint(3, 8))
                if status == 'delivered':
                    shipment.actual_arrival = now - timedelta(days=random.randint(0, 2))
                shipment.save()
                shipments.append(shipment)

                # Add items if available
                if items:
                    for _ in range(random.randint(1, 3)):
                        ShipmentItem.objects.create(
                            shipment=shipment,
                            item=random.choice(items),
                            quantity=Decimal(str(random.randint(1, 100))),
                            weight=Decimal(str(round(random.uniform(10.0, 500.0), 2))),
                            volume=Decimal(str(round(random.uniform(0.5, 50.0), 2))),
                        )

            self.stdout.write(f'  Created {len(shipments)} shipments with items.')

            # -----------------------------------------------------------------
            # TRACKING EVENTS
            # -----------------------------------------------------------------
            tracking_count = 0
            for shipment in shipments:
                if shipment.status in ('draft', 'booked'):
                    continue
                event_count = random.randint(2, 5)
                for j in range(event_count):
                    ShipmentTracking.objects.create(
                        shipment=shipment,
                        location=fake.city(),
                        status=random.choice(['picked_up', 'in_transit', 'at_hub']),
                        notes=fake.sentence(),
                        recorded_at=timezone.now() - timedelta(hours=random.randint(1, 200)),
                        recorded_by=random.choice(users),
                    )
                    tracking_count += 1
            self.stdout.write(f'  Created {tracking_count} tracking events.')

            # -----------------------------------------------------------------
            # FREIGHT BILLS
            # -----------------------------------------------------------------
            bill_statuses = ['draft', 'pending_review', 'approved', 'paid', 'disputed']
            freight_bills = []
            for i in range(5):
                shipment = random.choice(shipments)
                bill = FreightBill(
                    tenant=tenant,
                    shipment=shipment,
                    carrier=shipment.carrier,
                    invoice_number=f'INV-{fake.random_number(digits=6)}',
                    invoice_date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                    due_date=timezone.now().date() + timedelta(days=random.randint(15, 60)),
                    amount=Decimal(str(round(random.uniform(500.0, 25000.0), 2))),
                    currency=random.choice(currencies),
                    status=bill_statuses[i],
                )
                if bill.status in ('approved', 'paid', 'disputed'):
                    bill.audited_by = random.choice(users)
                    bill.audited_at = timezone.now() - timedelta(days=random.randint(1, 10))
                if bill.status == 'paid':
                    bill.payment_date = timezone.now().date() - timedelta(days=random.randint(0, 5))
                    bill.payment_reference = f'PAY-{fake.random_number(digits=8)}'
                if bill.status == 'disputed':
                    bill.dispute_reason = fake.paragraph(nb_sentences=2)
                bill.save()
                freight_bills.append(bill)

                # Add bill items
                charge_types = ['base_freight', 'fuel_surcharge', 'handling', 'insurance', 'toll']
                for ctype in random.sample(charge_types, random.randint(1, 3)):
                    price = Decimal(str(round(random.uniform(50.0, 5000.0), 2)))
                    FreightBillItem.objects.create(
                        freight_bill=bill,
                        description=f'{ctype.replace("_", " ").title()} charge',
                        quantity=Decimal('1'),
                        unit_price=price,
                        total_price=price,
                        charge_type=ctype,
                    )
            self.stdout.write(f'  Created {len(freight_bills)} freight bills with items.')

            # -----------------------------------------------------------------
            # LOAD PLANS
            # -----------------------------------------------------------------
            vehicle_types = ['truck_20ft', 'truck_40ft', 'container_20ft', 'container_40ft', 'van', 'refrigerated']
            load_statuses = ['draft', 'planned', 'loading', 'loaded', 'closed']

            load_plans = []
            for i in range(5):
                max_wt = Decimal(str(round(random.uniform(5000.0, 30000.0), 2)))
                max_vol = Decimal(str(round(random.uniform(30.0, 100.0), 2)))
                planned_wt = Decimal(str(round(float(max_wt) * random.uniform(0.4, 0.95), 2)))
                planned_vol = Decimal(str(round(float(max_vol) * random.uniform(0.3, 0.9), 2)))

                load = LoadPlan(
                    tenant=tenant,
                    shipment=random.choice(shipments),
                    vehicle_type=random.choice(vehicle_types),
                    max_weight=max_wt,
                    max_volume=max_vol,
                    planned_weight=planned_wt,
                    planned_volume=planned_vol,
                    status=load_statuses[i],
                    planned_by=random.choice(users),
                )
                load.save()
                load_plans.append(load)

                # Add load items if items available
                if items:
                    for seq in range(1, random.randint(2, 4)):
                        LoadPlanItem.objects.create(
                            load_plan=load,
                            item=random.choice(items),
                            quantity=Decimal(str(random.randint(10, 200))),
                            weight=Decimal(str(round(random.uniform(50.0, 2000.0), 2))),
                            volume=Decimal(str(round(random.uniform(1.0, 20.0), 2))),
                            load_sequence=seq,
                        )
            self.stdout.write(f'  Created {len(load_plans)} load plans with items.')

        self.stdout.write(self.style.SUCCESS(
            '\nTMS seeding completed successfully!'
        ))
        self.stdout.write(self.style.WARNING(
            '\nNote: Login as a tenant admin (e.g., admin_<tenant-slug>) to see TMS data.'
        ))
        self.stdout.write(self.style.WARNING(
            'Superuser "admin" has no tenant — data won\'t appear when logged in as admin.'
        ))
