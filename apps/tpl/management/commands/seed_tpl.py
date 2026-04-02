import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.inventory.models import Warehouse
from apps.tpl.models import (
    BillingInvoice,
    BillingInvoiceItem,
    BillingRate,
    Client,
    ClientInventoryItem,
    ClientStorageZone,
    IntegrationConfig,
    IntegrationLog,
    RentalAgreement,
    SLA,
    SLAMetric,
    SpaceUsageRecord,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample 3PL Management data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete existing 3PL data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing 3PL data...')
            SpaceUsageRecord.objects.all().delete()
            RentalAgreement.objects.all().delete()
            IntegrationLog.objects.all().delete()
            IntegrationConfig.objects.all().delete()
            SLAMetric.objects.all().delete()
            SLA.objects.all().delete()
            ClientInventoryItem.objects.all().delete()
            ClientStorageZone.objects.all().delete()
            BillingInvoiceItem.objects.all().delete()
            BillingInvoice.objects.all().delete()
            BillingRate.objects.all().delete()
            Client.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Flushed.'))

        today = timezone.now().date()
        now = timezone.now()

        for tenant in tenants:
            self.stdout.write(f'\nSeeding 3PL data for tenant: {tenant.name}')

            users = list(User.objects.filter(tenant=tenant, is_active=True)[:5])
            if not users:
                self.stdout.write(self.style.WARNING(f'  No users for {tenant.name}. Skipping.'))
                continue

            if Client.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    f'  Data already exists for {tenant.name}. Use --flush to re-seed.'
                ))
                continue

            warehouses = list(Warehouse.objects.filter(tenant=tenant, is_active=True)[:3])

            # -----------------------------------------------------------------
            # 1. Clients (5)
            # -----------------------------------------------------------------
            client_data = [
                ('Apex Retail Group', 'John Carter', 'john@apexretail.com', '+1-555-0101', 'New York', 'USA', 'USD'),
                ('Global Foods Inc.', 'Sarah Chen', 'sarah@globalfoods.com', '+1-555-0102', 'Chicago', 'USA', 'USD'),
                ('EuroTech Solutions', 'Hans Mueller', 'hans@eurotech.de', '+49-30-5550103', 'Berlin', 'Germany', 'EUR'),
                ('MidEast Trading LLC', 'Ahmed Al-Rashid', 'ahmed@mideast.ae', '+971-4-5550104', 'Dubai', 'UAE', 'AED'),
                ('Pacific Pharma Ltd.', 'Yuki Tanaka', 'yuki@pacificpharma.jp', '+81-3-5550105', 'Tokyo', 'Japan', 'USD'),
            ]

            clients = []
            statuses = ['active', 'active', 'active', 'draft', 'active']
            for i, (name, contact, email, phone, city, country, currency) in enumerate(client_data):
                client = Client.objects.create(
                    tenant=tenant,
                    name=name,
                    contact_person=contact,
                    email=email,
                    phone=phone,
                    city=city,
                    country=country,
                    default_currency=currency,
                    status=statuses[i],
                    contract_start_date=today - timedelta(days=random.randint(90, 365)),
                    contract_end_date=today + timedelta(days=random.randint(180, 730)),
                    notes=f'Key 3PL client for {city} region.',
                    created_by=random.choice(users),
                )
                clients.append(client)
            self.stdout.write(f'  Created {len(clients)} clients.')

            active_clients = [c for c in clients if c.status == 'active']

            # -----------------------------------------------------------------
            # 2. Billing Rates (8)
            # -----------------------------------------------------------------
            rate_data = [
                ('storage', 'Pallet Storage - Standard', 'pallet/day', Decimal('2.50')),
                ('storage', 'Pallet Storage - Cold', 'pallet/day', Decimal('4.75')),
                ('transaction', 'Order Processing Fee', 'order', Decimal('3.00')),
                ('transaction', 'Pick & Pack Fee', 'line item', Decimal('0.75')),
                ('weight', 'Freight Handling - Inbound', 'kg', Decimal('0.15')),
                ('weight', 'Freight Handling - Outbound', 'kg', Decimal('0.18')),
                ('fixed', 'Monthly Management Fee', 'month', Decimal('500.00')),
                ('fixed', 'IT Integration Support', 'month', Decimal('250.00')),
            ]

            rates = []
            for rate_type, desc, uom, amount in rate_data:
                client = random.choice(active_clients)
                rate = BillingRate.objects.create(
                    tenant=tenant,
                    client=client,
                    rate_type=rate_type,
                    description=desc,
                    unit_of_measure=uom,
                    rate_amount=amount,
                    currency=client.default_currency,
                    effective_date=today - timedelta(days=random.randint(30, 180)),
                    is_active=True,
                    created_by=random.choice(users),
                )
                rates.append(rate)
            self.stdout.write(f'  Created {len(rates)} billing rates.')

            # -----------------------------------------------------------------
            # 3. Billing Invoices (4) with Line Items
            # -----------------------------------------------------------------
            invoice_statuses = ['draft', 'sent', 'paid', 'overdue']
            invoices = []
            for i in range(4):
                client = active_clients[i % len(active_clients)]
                period_start = today - timedelta(days=30 * (i + 1))
                period_end = period_start + timedelta(days=29)
                subtotal = Decimal(str(random.randint(2000, 15000)))
                tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
                total = subtotal + tax

                invoice = BillingInvoice.objects.create(
                    tenant=tenant,
                    client=client,
                    status=invoice_statuses[i],
                    billing_period_start=period_start,
                    billing_period_end=period_end,
                    subtotal=subtotal,
                    tax_amount=tax,
                    total_amount=total,
                    currency=client.default_currency,
                    due_date=period_end + timedelta(days=30),
                    issued_date=period_end + timedelta(days=1) if i > 0 else None,
                    created_by=random.choice(users),
                )
                invoices.append(invoice)

                for j in range(random.randint(2, 5)):
                    rate = random.choice(rates)
                    qty = Decimal(str(random.randint(10, 500)))
                    unit_price = rate.rate_amount
                    BillingInvoiceItem.objects.create(
                        invoice=invoice,
                        description=rate.description,
                        rate=rate,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=(qty * unit_price).quantize(Decimal('0.01')),
                    )
            self.stdout.write(f'  Created {len(invoices)} invoices with line items.')

            # -----------------------------------------------------------------
            # 4. Client Storage Zones (6)
            # -----------------------------------------------------------------
            zone_data = [
                ('Zone A - Dry Goods', 'dedicated', Decimal('5000'), 'sqft'),
                ('Zone B - Cold Storage', 'dedicated', Decimal('2000'), 'sqft'),
                ('Zone C - Shared Bulk', 'shared', Decimal('200'), 'pallets'),
                ('Zone D - High Value', 'dedicated', Decimal('1500'), 'sqft'),
                ('Zone E - Overflow', 'shared', Decimal('150'), 'cbm'),
                ('Zone F - Receiving Dock', 'shared', Decimal('3000'), 'sqft'),
            ]

            zones = []
            for name, ztype, cap, unit in zone_data:
                zone = ClientStorageZone.objects.create(
                    tenant=tenant,
                    client=random.choice(active_clients),
                    warehouse=random.choice(warehouses) if warehouses else None,
                    zone_name=name,
                    zone_type=ztype,
                    location_description=f'{name} area',
                    capacity=cap,
                    capacity_unit=unit,
                    is_active=True,
                    created_by=random.choice(users),
                )
                zones.append(zone)
            self.stdout.write(f'  Created {len(zones)} storage zones.')

            # -----------------------------------------------------------------
            # 5. Client Inventory Items (10)
            # -----------------------------------------------------------------
            item_data = [
                ('Electronics - Laptops', 'SKU-LAP-001', 150, 'units', 450, 'kg'),
                ('Electronics - Phones', 'SKU-PHN-002', 500, 'units', 100, 'kg'),
                ('Food - Canned Goods', 'SKU-CAN-003', 2000, 'cases', 4500, 'kg'),
                ('Food - Frozen Meals', 'SKU-FRZ-004', 800, 'cases', 2400, 'kg'),
                ('Pharma - Vaccines', 'SKU-VAC-005', 300, 'boxes', 75, 'kg'),
                ('Apparel - T-Shirts', 'SKU-TSH-006', 3000, 'units', 600, 'kg'),
                ('Auto Parts - Filters', 'SKU-FLT-007', 1200, 'units', 900, 'kg'),
                ('Chemicals - Cleaners', 'SKU-CLN-008', 400, 'drums', 8000, 'kg'),
                ('Paper Products', 'SKU-PPR-009', 1500, 'pallets', 12000, 'kg'),
                ('Beverages - Bottled', 'SKU-BEV-010', 5000, 'cases', 15000, 'kg'),
            ]

            for name, sku, qty, uom, wt, wu in item_data:
                ClientInventoryItem.objects.create(
                    tenant=tenant,
                    client=random.choice(active_clients),
                    storage_zone=random.choice(zones),
                    item_name=name,
                    sku=sku,
                    quantity=Decimal(str(qty)),
                    unit_of_measure=uom,
                    weight=Decimal(str(wt)),
                    weight_unit=wu,
                    received_date=today - timedelta(days=random.randint(1, 60)),
                    created_by=random.choice(users),
                )
            self.stdout.write('  Created 10 inventory items.')

            # -----------------------------------------------------------------
            # 6. SLAs (3) with Metrics
            # -----------------------------------------------------------------
            sla_data = [
                ('Premium Service Agreement', 'active', 'monthly'),
                ('Standard Service Agreement', 'active', 'quarterly'),
                ('Basic Service Agreement', 'draft', 'monthly'),
            ]

            for title, status, freq in sla_data:
                client = random.choice(active_clients)
                sla = SLA.objects.create(
                    tenant=tenant,
                    client=client,
                    title=title,
                    status=status,
                    effective_date=today - timedelta(days=random.randint(60, 180)),
                    expiry_date=today + timedelta(days=random.randint(180, 365)),
                    review_frequency=freq,
                    description=f'{title} for {client.name}.',
                    penalty_clause='Penalty of 5% of monthly fees per SLA breach.',
                    created_by=random.choice(users),
                )

                metrics = [
                    ('On-Time Delivery Rate', 'on_time_delivery', Decimal('98.00'), '%'),
                    ('Order Accuracy Rate', 'order_accuracy', Decimal('99.50'), '%'),
                    ('Turnaround Time', 'turnaround_time', Decimal('24.00'), 'hours'),
                    ('Damage Rate', 'damage_rate', Decimal('0.50'), '%'),
                ]
                for mname, mtype, target, unit in metrics:
                    actual = target + Decimal(str(random.uniform(-3, 2))).quantize(Decimal('0.01'))
                    is_breached = (mtype == 'damage_rate' and actual > target) or (mtype != 'damage_rate' and actual < target)
                    SLAMetric.objects.create(
                        sla=sla,
                        metric_name=mname,
                        metric_type=mtype,
                        target_value=target,
                        actual_value=actual,
                        unit=unit,
                        measurement_period='March 2026',
                        is_breached=is_breached,
                        breach_notes='Auto-flagged during seeding.' if is_breached else '',
                    )
            self.stdout.write('  Created 3 SLAs with metrics.')

            # -----------------------------------------------------------------
            # 7. Integration Configs (3) with Logs
            # -----------------------------------------------------------------
            integration_data = [
                ('SAP ERP Sync', 'active', 'bidirectional', 'daily'),
                ('Shopify Orders Import', 'active', 'inbound', 'hourly'),
                ('Custom REST API', 'draft', 'outbound', 'manual'),
            ]

            for iname, status, direction, freq in integration_data:
                client = random.choice(active_clients)
                config = IntegrationConfig.objects.create(
                    tenant=tenant,
                    client=client,
                    integration_name=iname,
                    status=status,
                    api_key=f'tpl_key_{random.randint(100000, 999999)}',
                    api_endpoint=f'https://api.example.com/{iname.lower().replace(" ", "-")}',
                    webhook_url=f'https://hooks.example.com/{iname.lower().replace(" ", "-")}' if direction != 'outbound' else '',
                    sync_direction=direction,
                    sync_frequency=freq,
                    last_sync_at=now - timedelta(hours=random.randint(1, 48)) if status == 'active' else None,
                    created_by=random.choice(users),
                )

                if status == 'active':
                    for j in range(3):
                        log_status = random.choice(['success', 'success', 'success', 'partial', 'failed'])
                        started = now - timedelta(hours=random.randint(1, 168))
                        IntegrationLog.objects.create(
                            integration=config,
                            log_type='sync',
                            direction=random.choice(['inbound', 'outbound']),
                            status=log_status,
                            records_processed=random.randint(50, 500),
                            records_failed=random.randint(0, 10) if log_status != 'success' else 0,
                            error_message='Connection timeout' if log_status == 'failed' else '',
                            started_at=started,
                            completed_at=started + timedelta(minutes=random.randint(1, 30)),
                        )
            self.stdout.write('  Created 3 integrations with logs.')

            # -----------------------------------------------------------------
            # 8. Rental Agreements (3) with Usage Records
            # -----------------------------------------------------------------
            rental_data = [
                ('dedicated', Decimal('10000'), 'sqft', Decimal('5000'), 'monthly'),
                ('shared', Decimal('200'), 'pallets', Decimal('800'), 'monthly'),
                ('dedicated', Decimal('500'), 'sqm', Decimal('3500'), 'monthly'),
            ]

            rental_statuses = ['active', 'active', 'draft']
            for i, (stype, area, aunit, rate, period) in enumerate(rental_data):
                client = active_clients[i % len(active_clients)]
                rental = RentalAgreement.objects.create(
                    tenant=tenant,
                    client=client,
                    status=rental_statuses[i],
                    space_type=stype,
                    warehouse=warehouses[i] if i < len(warehouses) else None,
                    area_size=area,
                    area_unit=aunit,
                    rate_amount=rate,
                    rate_period=period,
                    currency=client.default_currency,
                    start_date=today - timedelta(days=random.randint(60, 180)),
                    end_date=today + timedelta(days=random.randint(180, 365)),
                    terms='Standard warehouse rental terms apply.',
                    created_by=random.choice(users),
                )

                if rental.status == 'active':
                    for m in range(3):
                        p_start = today - timedelta(days=30 * (m + 1))
                        p_end = p_start + timedelta(days=29)
                        used = area * Decimal(str(random.uniform(0.6, 0.95))).quantize(Decimal('0.01'))
                        util = ((used / area) * 100).quantize(Decimal('0.01'))
                        charge = (rate * Decimal(str(random.uniform(0.8, 1.1)))).quantize(Decimal('0.01'))
                        SpaceUsageRecord.objects.create(
                            agreement=rental,
                            period_start=p_start,
                            period_end=p_end,
                            area_used=used,
                            utilization_percentage=util,
                            calculated_charge=charge,
                        )
            self.stdout.write('  Created 3 rental agreements with usage records.')

        self.stdout.write(self.style.SUCCESS('\n3PL Management seeding complete!'))
        self.stdout.write(self.style.WARNING(
            "\nNote: Superuser 'admin' has no tenant — data won't appear when logged in as admin."
        ))
        self.stdout.write('Log in as a tenant admin (e.g., admin_<slug>) to see 3PL data.')
