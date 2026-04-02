import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.finance.models import (
    APInvoice, APInvoiceItem, APPayment,
    ARInvoice, ARInvoiceItem, ARPayment,
    LandedCostSheet, LandedCostComponent,
    Budget, BudgetEntry,
    TaxRate, TaxTransaction,
)
from apps.procurement.models import Vendor, PurchaseOrder
from apps.oms.models import Customer, Order
from apps.tms.models import Carrier, Shipment

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample Finance & Accounting data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete existing Finance data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing Finance data...')
            TaxTransaction.objects.all().delete()
            TaxRate.objects.all().delete()
            BudgetEntry.objects.all().delete()
            Budget.objects.all().delete()
            LandedCostComponent.objects.all().delete()
            LandedCostSheet.objects.all().delete()
            ARPayment.objects.all().delete()
            ARInvoiceItem.objects.all().delete()
            ARInvoice.objects.all().delete()
            APPayment.objects.all().delete()
            APInvoiceItem.objects.all().delete()
            APInvoice.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Flushed.'))

        today = timezone.now().date()
        now = timezone.now()

        for tenant in tenants:
            self.stdout.write(f'\nSeeding Finance data for tenant: {tenant.name}')

            users = list(User.objects.filter(tenant=tenant, is_active=True)[:5])
            if not users:
                self.stdout.write(self.style.WARNING(f'  No users for {tenant.name}. Skipping.'))
                continue

            if TaxRate.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    f'  Data already exists for {tenant.name}. Use --flush to re-seed.'
                ))
                continue

            # Cross-module data
            vendors = list(Vendor.objects.filter(tenant=tenant)[:5])
            customers = list(Customer.objects.filter(tenant=tenant)[:5])
            purchase_orders = list(PurchaseOrder.objects.filter(tenant=tenant)[:5])
            orders = list(Order.objects.filter(tenant=tenant)[:5])
            carriers = list(Carrier.objects.filter(tenant=tenant)[:3])
            shipments = list(Shipment.objects.filter(tenant=tenant)[:5])

            # -----------------------------------------------------------------
            # 1. Tax Rates (6)
            # -----------------------------------------------------------------
            tax_rate_data = [
                ('TAX-USSCA', 'US Sales Tax - CA', 'sales_tax', Decimal('8.2500'), 'USA', 'California'),
                ('TAX-UKVAT', 'UK VAT Standard', 'vat', Decimal('20.0000'), 'UK', ''),
                ('TAX-UAEVAT', 'UAE VAT', 'vat', Decimal('5.0000'), 'UAE', ''),
                ('TAX-CUSDUTY', 'Import Customs Duty', 'customs_duty', Decimal('12.0000'), '', ''),
                ('TAX-EXCFUEL', 'Excise Tax - Fuel', 'excise', Decimal('2.5000'), 'USA', ''),
                ('TAX-WHPK', 'Withholding Tax', 'withholding', Decimal('10.0000'), 'Pakistan', ''),
            ]

            tax_rates = []
            for code, name, ttype, rate, country, region in tax_rate_data:
                tr = TaxRate.objects.create(
                    tenant=tenant,
                    code=code,
                    name=name,
                    tax_type=ttype,
                    rate=rate,
                    country=country,
                    region=region,
                    is_active=True,
                    effective_from=today - timedelta(days=365),
                )
                tax_rates.append(tr)
            self.stdout.write(f'  Created {len(tax_rates)} tax rates.')

            # -----------------------------------------------------------------
            # 2. AP Invoices (4) with Line Items and Payments
            # -----------------------------------------------------------------
            ap_statuses = ['draft', 'approved', 'partially_paid', 'paid']
            ap_item_descs = [
                'Raw Materials - Steel', 'Packaging Supplies', 'Office Equipment',
                'Maintenance Parts', 'Chemical Reagents', 'Safety Gear',
                'Electrical Components', 'Lubricants & Oils',
            ]
            ap_invoices = []

            for i in range(4):
                vendor = random.choice(vendors) if vendors else None
                po = random.choice(purchase_orders) if purchase_orders else None
                subtotal = Decimal(str(random.randint(1000, 20000)))
                tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
                total = subtotal + tax
                inv_date = today - timedelta(days=random.randint(10, 90))

                ap_inv = APInvoice.objects.create(
                    tenant=tenant,
                    vendor=vendor,
                    purchase_order=po,
                    invoice_date=inv_date,
                    due_date=inv_date + timedelta(days=30),
                    subtotal=subtotal,
                    tax_amount=tax,
                    total_amount=total,
                    amount_paid=Decimal('0'),
                    status=ap_statuses[i],
                    payment_terms='net_30',
                    notes=f'AP Invoice for {vendor.name if vendor else "vendor"}.',
                    created_by=random.choice(users),
                )
                ap_invoices.append(ap_inv)

                # Line items
                num_items = random.randint(2, 4)
                for j in range(num_items):
                    qty = Decimal(str(random.randint(5, 100)))
                    unit_price = Decimal(str(random.randint(10, 500)))
                    APInvoiceItem.objects.create(
                        invoice=ap_inv,
                        description=random.choice(ap_item_descs),
                        quantity=qty,
                        unit_price=unit_price,
                        tax_rate=Decimal('10.00'),
                        total_price=(qty * unit_price).quantize(Decimal('0.01')),
                    )

                # Payments for partially_paid / paid
                if ap_statuses[i] == 'partially_paid':
                    pay_amount = (total * Decimal('0.50')).quantize(Decimal('0.01'))
                    APPayment.objects.create(
                        tenant=tenant,
                        invoice=ap_inv,
                        payment_date=inv_date + timedelta(days=15),
                        amount=pay_amount,
                        payment_method='bank_transfer',
                        reference_number=f'REF-AP-{random.randint(10000, 99999)}',
                        notes='Partial payment.',
                        created_by=random.choice(users),
                    )
                elif ap_statuses[i] == 'paid':
                    APPayment.objects.create(
                        tenant=tenant,
                        invoice=ap_inv,
                        payment_date=inv_date + timedelta(days=20),
                        amount=total,
                        payment_method='wire',
                        reference_number=f'REF-AP-{random.randint(10000, 99999)}',
                        notes='Full payment.',
                        created_by=random.choice(users),
                    )

            self.stdout.write(f'  Created {len(ap_invoices)} AP invoices with line items.')

            # -----------------------------------------------------------------
            # 3. AR Invoices (4) with Line Items and Payments
            # -----------------------------------------------------------------
            ar_statuses = ['draft', 'sent', 'partially_paid', 'paid']
            ar_item_descs = [
                'Product A - Bulk Order', 'Service Fee - Consulting',
                'License Renewal', 'Freight Charge',
                'Custom Fabrication', 'Support Package',
                'Training Session', 'Subscription - Annual',
            ]
            ar_invoices = []

            for i in range(4):
                customer = random.choice(customers) if customers else None
                order = random.choice(orders) if orders else None
                subtotal = Decimal(str(random.randint(1000, 20000)))
                tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
                total = subtotal + tax
                inv_date = today - timedelta(days=random.randint(10, 90))

                ar_inv = ARInvoice.objects.create(
                    tenant=tenant,
                    customer=customer,
                    order=order,
                    invoice_date=inv_date,
                    due_date=inv_date + timedelta(days=30),
                    subtotal=subtotal,
                    tax_amount=tax,
                    total_amount=total,
                    amount_received=Decimal('0'),
                    status=ar_statuses[i],
                    notes=f'AR Invoice for {customer.name if customer else "customer"}.',
                    created_by=random.choice(users),
                )
                ar_invoices.append(ar_inv)

                # Line items
                num_items = random.randint(2, 4)
                for j in range(num_items):
                    qty = Decimal(str(random.randint(1, 50)))
                    unit_price = Decimal(str(random.randint(50, 1000)))
                    ARInvoiceItem.objects.create(
                        invoice=ar_inv,
                        description=random.choice(ar_item_descs),
                        quantity=qty,
                        unit_price=unit_price,
                        tax_rate=Decimal('10.00'),
                        total_price=(qty * unit_price).quantize(Decimal('0.01')),
                    )

                # Payments for partially_paid / paid
                if ar_statuses[i] == 'partially_paid':
                    pay_amount = (total * Decimal('0.50')).quantize(Decimal('0.01'))
                    ARPayment.objects.create(
                        tenant=tenant,
                        invoice=ar_inv,
                        payment_date=inv_date + timedelta(days=15),
                        amount=pay_amount,
                        payment_method='bank_transfer',
                        reference_number=f'REF-AR-{random.randint(10000, 99999)}',
                        notes='Partial payment received.',
                        created_by=random.choice(users),
                    )
                elif ar_statuses[i] == 'paid':
                    ARPayment.objects.create(
                        tenant=tenant,
                        invoice=ar_inv,
                        payment_date=inv_date + timedelta(days=20),
                        amount=total,
                        payment_method='credit_card',
                        reference_number=f'REF-AR-{random.randint(10000, 99999)}',
                        notes='Full payment received.',
                        created_by=random.choice(users),
                    )

            self.stdout.write(f'  Created {len(ar_invoices)} AR invoices with line items.')

            # -----------------------------------------------------------------
            # 4. Landed Cost Sheets (3) with Components
            # -----------------------------------------------------------------
            lc_statuses = ['draft', 'calculated', 'finalized']
            component_pool = [
                ('freight', 'International Freight Charges'),
                ('customs_duty', 'Import Customs Duty'),
                ('insurance', 'Cargo Insurance Premium'),
                ('handling', 'Port Handling Fees'),
                ('inspection', 'Quality Inspection Fee'),
                ('warehousing', 'Temporary Warehousing'),
                ('brokerage', 'Customs Brokerage Fee'),
                ('other', 'Documentation Charges'),
            ]
            lc_sheets = []

            for i in range(3):
                goods_cost = Decimal(str(random.randint(5000, 50000)))
                shipment = random.choice(shipments) if shipments else None
                po = random.choice(purchase_orders) if purchase_orders else None
                carrier = random.choice(carriers) if carriers else None

                sheet = LandedCostSheet.objects.create(
                    tenant=tenant,
                    shipment=shipment,
                    purchase_order=po,
                    carrier=carrier,
                    total_goods_cost=goods_cost,
                    total_landed_cost=goods_cost,
                    status=lc_statuses[i],
                    notes=f'Landed cost calculation for shipment.',
                    created_by=random.choice(users),
                )

                # Components
                num_components = random.randint(3, 5)
                selected_components = random.sample(component_pool, num_components)
                total_additional = Decimal('0')
                for cost_type, desc in selected_components:
                    amount = Decimal(str(random.randint(200, 5000)))
                    total_additional += amount
                    LandedCostComponent.objects.create(
                        sheet=sheet,
                        cost_type=cost_type,
                        description=desc,
                        amount=amount,
                        allocation_method=random.choice(['by_value', 'by_weight', 'by_quantity', 'equal']),
                    )

                # Update total_landed_cost for calculated/finalized
                if lc_statuses[i] in ('calculated', 'finalized'):
                    sheet.total_landed_cost = goods_cost + total_additional
                    sheet.save()

                lc_sheets.append(sheet)

            self.stdout.write(f'  Created {len(lc_sheets)} landed cost sheets with components.')

            # -----------------------------------------------------------------
            # 5. Budgets (3) with Entries
            # -----------------------------------------------------------------
            budget_data = [
                ('Procurement Budget', 'Procurement', 'monthly', Decimal('50000'), 'draft'),
                ('Logistics Budget', 'Logistics', 'quarterly', Decimal('150000'), 'active'),
                ('Warehouse Budget', 'Warehouse', 'annual', Decimal('500000'), 'active'),
            ]

            for bname, dept, period_type, planned, status in budget_data:
                if period_type == 'monthly':
                    p_start = today.replace(day=1)
                    p_end = (p_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
                elif period_type == 'quarterly':
                    quarter_month = ((today.month - 1) // 3) * 3 + 1
                    p_start = today.replace(month=quarter_month, day=1)
                    p_end = (p_start + timedelta(days=93)).replace(day=1) - timedelta(days=1)
                else:
                    p_start = today.replace(month=1, day=1)
                    p_end = today.replace(month=12, day=31)

                budget = Budget.objects.create(
                    tenant=tenant,
                    name=bname,
                    department=dept,
                    category='Operations',
                    period_type=period_type,
                    period_start=p_start,
                    period_end=p_end,
                    planned_amount=planned,
                    actual_amount=Decimal('0'),
                    status=status,
                    notes=f'{dept} department budget for current period.',
                    created_by=random.choice(users),
                )

                # Budget entries for active budgets
                if status == 'active':
                    entry_descs = [
                        'Vendor payment', 'Equipment purchase', 'Maintenance cost',
                        'Fuel expenses', 'Staff overtime', 'Software license',
                        'Training expenses', 'Travel costs',
                    ]
                    num_entries = random.randint(3, 5)
                    for j in range(num_entries):
                        entry_amount = Decimal(str(random.randint(1000, int(planned / 5))))
                        BudgetEntry.objects.create(
                            budget=budget,
                            entry_date=today - timedelta(days=random.randint(1, 60)),
                            description=random.choice(entry_descs),
                            amount=entry_amount,
                            reference_type=random.choice(['AP Invoice', 'PO', 'Expense']),
                            reference_number=f'REF-{random.randint(10000, 99999)}',
                            created_by=random.choice(users),
                        )

            self.stdout.write('  Created 3 budgets with entries.')

            # -----------------------------------------------------------------
            # 6. Tax Transactions (5)
            # -----------------------------------------------------------------
            tx_types = ['collected', 'collected', 'paid', 'paid', 'refund']
            tx_ref_types = ['AR Invoice', 'AR Invoice', 'AP Invoice', 'AP Invoice', 'AP Invoice']

            for i in range(5):
                tr = random.choice(tax_rates)
                taxable = Decimal(str(random.randint(5000, 50000)))
                tax_amt = (taxable * tr.rate / Decimal('100')).quantize(Decimal('0.01'))

                TaxTransaction.objects.create(
                    tenant=tenant,
                    tax_rate=tr,
                    transaction_type=tx_types[i],
                    taxable_amount=taxable,
                    tax_amount=tax_amt,
                    transaction_date=today - timedelta(days=random.randint(1, 90)),
                    reference_type=tx_ref_types[i],
                    reference_number=f'TX-REF-{random.randint(10000, 99999)}',
                    notes=f'Tax transaction - {tx_types[i]}.',
                    created_by=random.choice(users),
                )

            self.stdout.write('  Created 5 tax transactions.')

        self.stdout.write(self.style.SUCCESS('\nFinance & Accounting seeding complete!'))
        self.stdout.write(self.style.WARNING(
            "\nNote: Superuser 'admin' has no tenant — data won't appear when logged in as admin."
        ))
        self.stdout.write('Log in as a tenant admin (e.g., admin_<slug>) to see Finance data.')
