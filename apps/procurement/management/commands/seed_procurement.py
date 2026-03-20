"""
Management command to seed the database with fake procurement data.

Usage:
    python manage.py seed_procurement
    python manage.py seed_procurement --flush  (clears procurement data first)

Requires: Tenants and users must exist first (run seed_data first).
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.procurement.models import (
    GoodsReceiptNote,
    GRNItem,
    Item,
    ItemCategory,
    POAcknowledgement,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RFQ,
    RFQItem,
    RFQVendor,
    ShipmentUpdate,
    ThreeWayMatch,
    Vendor,
    VendorContact,
    VendorInvoice,
    VendorInvoiceItem,
    VendorQuote,
)

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake procurement data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing procurement data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing procurement data...'))
            ThreeWayMatch.objects.all().delete()
            VendorInvoiceItem.objects.all().delete()
            VendorInvoice.objects.all().delete()
            GRNItem.objects.all().delete()
            GoodsReceiptNote.objects.all().delete()
            ShipmentUpdate.objects.all().delete()
            POAcknowledgement.objects.all().delete()
            VendorContact.objects.all().delete()
            PurchaseOrderItem.objects.all().delete()
            PurchaseOrder.objects.all().delete()
            VendorQuote.objects.all().delete()
            RFQVendor.objects.all().delete()
            RFQItem.objects.all().delete()
            RFQ.objects.all().delete()
            PurchaseRequisitionItem.objects.all().delete()
            PurchaseRequisition.objects.all().delete()
            Item.objects.all().delete()
            ItemCategory.objects.all().delete()
            Vendor.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All procurement data flushed.'))

        for tenant in tenants:
            self.stdout.write(f'\nSeeding procurement data for: {tenant.name}')
            users = list(User.objects.filter(tenant=tenant, is_active=True))

            if not users:
                self.stdout.write(self.style.WARNING(f'  No users found, skipping.'))
                continue

            categories = self._create_categories(tenant)
            items = self._create_items(tenant, categories)
            vendors = self._create_vendors(tenant, users)
            self._create_vendor_contacts(tenant, vendors)
            requisitions = self._create_requisitions(tenant, users, items)
            rfqs = self._create_rfqs(tenant, users, items, vendors, requisitions)
            purchase_orders = self._create_purchase_orders(tenant, users, items, vendors, rfqs, requisitions)
            grns = self._create_grns(tenant, users, purchase_orders)
            invoices = self._create_invoices(tenant, vendors, purchase_orders, grns)
            self._create_three_way_matches(tenant, purchase_orders, grns, invoices)
            self._create_shipment_updates(tenant, vendors, purchase_orders)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Procurement seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

    def _create_categories(self, tenant):
        category_data = [
            ('Office Supplies', 'office-supplies', 'Stationery, paper, pens, and general office items'),
            ('IT Equipment', 'it-equipment', 'Computers, monitors, keyboards, and peripherals'),
            ('Furniture', 'furniture', 'Desks, chairs, cabinets, and shelving units'),
            ('Raw Materials', 'raw-materials', 'Raw materials for production and manufacturing'),
            ('Cleaning Supplies', 'cleaning-supplies', 'Cleaning products and janitorial equipment'),
            ('Safety Equipment', 'safety-equipment', 'PPE, fire extinguishers, and safety gear'),
            ('Packaging Materials', 'packaging-materials', 'Boxes, tape, bubble wrap, and labels'),
            ('Electrical Components', 'electrical-components', 'Wires, switches, circuit boards, and connectors'),
            ('Tools & Hardware', 'tools-hardware', 'Hand tools, power tools, and hardware supplies'),
            ('Services', 'services', 'Professional services, consulting, and maintenance'),
        ]

        categories = []
        for name, slug, desc in category_data:
            cat, created = ItemCategory.objects.get_or_create(
                tenant=tenant,
                slug=slug,
                defaults={'name': name, 'description': desc, 'is_active': True},
            )
            categories.append(cat)

        self.stdout.write(f'  Created {len(categories)} item categories')
        return categories

    def _create_items(self, tenant, categories):
        items_data = [
            # Office Supplies
            ('A4 Paper Ream', 'OFF-001', 0, 'piece', '4.50'),
            ('Ballpoint Pens (Box of 12)', 'OFF-002', 0, 'box', '3.25'),
            ('Sticky Notes Pack', 'OFF-003', 0, 'pack', '2.75'),
            ('Printer Toner Cartridge', 'OFF-004', 0, 'piece', '45.00'),
            ('File Folders (Pack of 25)', 'OFF-005', 0, 'pack', '8.50'),
            # IT Equipment
            ('Laptop - Business Grade', 'IT-001', 1, 'piece', '1200.00'),
            ('24" Monitor', 'IT-002', 1, 'piece', '350.00'),
            ('Wireless Mouse', 'IT-003', 1, 'piece', '25.00'),
            ('USB-C Docking Station', 'IT-004', 1, 'piece', '180.00'),
            ('Ethernet Cable (3m)', 'IT-005', 1, 'piece', '8.00'),
            ('Mechanical Keyboard', 'IT-006', 1, 'piece', '75.00'),
            # Furniture
            ('Ergonomic Office Chair', 'FUR-001', 2, 'piece', '450.00'),
            ('Standing Desk (Electric)', 'FUR-002', 2, 'piece', '650.00'),
            ('3-Drawer Filing Cabinet', 'FUR-003', 2, 'piece', '180.00'),
            ('Bookshelf Unit', 'FUR-004', 2, 'piece', '120.00'),
            # Raw Materials
            ('Steel Rods (per kg)', 'RAW-001', 3, 'kg', '2.80'),
            ('Aluminum Sheets (per sq meter)', 'RAW-002', 3, 'meter', '15.00'),
            ('Copper Wire (per meter)', 'RAW-003', 3, 'meter', '4.50'),
            ('PVC Pipes (per meter)', 'RAW-004', 3, 'meter', '3.20'),
            ('Plywood Sheet (4x8)', 'RAW-005', 3, 'piece', '28.00'),
            # Cleaning Supplies
            ('Industrial Floor Cleaner (5L)', 'CLN-001', 4, 'piece', '12.00'),
            ('Microfiber Cloths (Pack of 10)', 'CLN-002', 4, 'pack', '8.50'),
            ('Hand Sanitizer (1L)', 'CLN-003', 4, 'piece', '6.00'),
            # Safety Equipment
            ('Safety Goggles', 'SAF-001', 5, 'piece', '12.00'),
            ('Hard Hat', 'SAF-002', 5, 'piece', '18.00'),
            ('Safety Gloves (Pair)', 'SAF-003', 5, 'piece', '8.50'),
            ('Fire Extinguisher (5kg)', 'SAF-004', 5, 'piece', '45.00'),
            # Packaging Materials
            ('Cardboard Box (Medium)', 'PKG-001', 6, 'piece', '1.50'),
            ('Bubble Wrap Roll (50m)', 'PKG-002', 6, 'piece', '18.00'),
            ('Packing Tape (Roll)', 'PKG-003', 6, 'piece', '3.50'),
            # Electrical Components
            ('LED Light Bulb (10W)', 'ELC-001', 7, 'piece', '5.50'),
            ('Power Strip (6 Outlet)', 'ELC-002', 7, 'piece', '12.00'),
            ('Extension Cord (5m)', 'ELC-003', 7, 'piece', '8.00'),
            # Tools & Hardware
            ('Screwdriver Set', 'TLS-001', 8, 'set', '22.00'),
            ('Cordless Drill', 'TLS-002', 8, 'piece', '85.00'),
            ('Measuring Tape (5m)', 'TLS-003', 8, 'piece', '6.00'),
            # Services
            ('IT Consulting (per hour)', 'SVC-001', 9, 'hour', '150.00'),
            ('Cleaning Service (per day)', 'SVC-002', 9, 'day', '200.00'),
            ('Equipment Maintenance', 'SVC-003', 9, 'unit', '350.00'),
        ]

        items = []
        for name, code, cat_idx, uom, price in items_data:
            item, created = Item.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    'name': name,
                    'description': fake.sentence(),
                    'category': categories[cat_idx],
                    'unit_of_measure': uom,
                    'unit_price': Decimal(price),
                    'is_active': True,
                },
            )
            items.append(item)

        self.stdout.write(f'  Created {len(items)} items')
        return items

    def _create_vendors(self, tenant, users):
        vendor_data = [
            ('Global Tech Supplies', 'VND-001', 'net_30'),
            ('Prime Office Solutions', 'VND-002', 'net_15'),
            ('MetalWorks Industries', 'VND-003', 'net_45'),
            ('SafetyFirst Equipment Co.', 'VND-004', 'net_30'),
            ('CleanPro Services Ltd.', 'VND-005', 'cod'),
            ('FurniCraft International', 'VND-006', 'net_60'),
            ('ElectroParts Wholesale', 'VND-007', 'net_30'),
            ('PackRight Solutions', 'VND-008', 'net_15'),
            ('ToolMaster Supply Co.', 'VND-009', 'advance'),
            ('QuickLogistics Transport', 'VND-010', 'net_30'),
            ('BrightStar Electronics', 'VND-011', 'net_45'),
            ('GreenSource Materials', 'VND-012', 'net_30'),
        ]

        vendors = []
        for name, code, terms in vendor_data:
            vendor, created = Vendor.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    'name': name,
                    'contact_person': fake.name(),
                    'email': fake.company_email(),
                    'phone': fake.phone_number()[:20],
                    'address': fake.address(),
                    'city': fake.city(),
                    'country': fake.country(),
                    'tax_id': fake.bothify('??-#######'),
                    'payment_terms': terms,
                    'is_active': True,
                    'created_by': random.choice(users),
                },
            )
            vendors.append(vendor)

        self.stdout.write(f'  Created {len(vendors)} vendors')
        return vendors

    def _create_vendor_contacts(self, tenant, vendors):
        count = 0
        for vendor in vendors:
            for i in range(random.randint(1, 3)):
                VendorContact.objects.get_or_create(
                    tenant=tenant,
                    vendor=vendor,
                    email=fake.email(),
                    defaults={
                        'name': fake.name(),
                        'phone': fake.phone_number()[:20],
                        'is_primary': i == 0,
                        'is_active': True,
                    },
                )
                count += 1
        self.stdout.write(f'  Created {count} vendor contacts')

    def _create_requisitions(self, tenant, users, items):
        departments = ['Engineering', 'Operations', 'Finance', 'Marketing', 'HR', 'IT', 'Warehouse']
        statuses = ['draft', 'pending_approval', 'approved', 'approved', 'approved', 'rejected', 'cancelled']
        priorities = ['low', 'medium', 'medium', 'high', 'urgent']

        requisitions = []
        for i in range(15):
            status = random.choice(statuses)
            requester = random.choice(users)
            pr = PurchaseRequisition(
                tenant=tenant,
                requisition_number=f'PR-{i + 1:05d}',
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=2),
                requested_by=requester,
                department=random.choice(departments),
                status=status,
                priority=random.choice(priorities),
                required_date=timezone.now().date() + timedelta(days=random.randint(7, 60)),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            if status in ('approved',):
                pr.approved_by = random.choice(users)
                pr.approved_at = timezone.now() - timedelta(days=random.randint(1, 10))
            pr.save()

            # Add 2-5 line items
            selected_items = random.sample(items, k=random.randint(2, 5))
            for item in selected_items:
                PurchaseRequisitionItem.objects.create(
                    requisition=pr,
                    item=item,
                    description=item.name,
                    quantity=Decimal(str(random.randint(1, 50))),
                    estimated_unit_price=item.unit_price,
                    notes=fake.sentence() if random.random() > 0.7 else '',
                )

            requisitions.append(pr)

        self.stdout.write(f'  Created {len(requisitions)} purchase requisitions')
        return requisitions

    def _create_rfqs(self, tenant, users, items, vendors, requisitions):
        approved_prs = [pr for pr in requisitions if pr.status == 'approved']
        statuses = ['draft', 'sent', 'sent', 'received', 'evaluated', 'closed', 'cancelled']

        rfqs = []
        for i in range(8):
            status = random.choice(statuses)
            linked_pr = random.choice(approved_prs) if approved_prs and random.random() > 0.3 else None

            rfq = RFQ(
                tenant=tenant,
                rfq_number=f'RFQ-{i + 1:05d}',
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=2),
                requisition=linked_pr,
                status=status,
                submission_deadline=timezone.now().date() + timedelta(days=random.randint(7, 30)),
                created_by=random.choice(users),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            rfq.save()

            # Add 2-4 items
            selected_items = random.sample(items, k=random.randint(2, 4))
            rfq_items = []
            for item in selected_items:
                rfq_item = RFQItem.objects.create(
                    rfq=rfq,
                    item=item,
                    description=item.name,
                    quantity=Decimal(str(random.randint(5, 100))),
                    unit_of_measure=item.unit_of_measure,
                )
                rfq_items.append(rfq_item)

            # Invite 2-4 vendors
            invited_vendors = random.sample(vendors, k=random.randint(2, 4))
            rfq_vendor_objs = []
            for vendor in invited_vendors:
                vendor_statuses = ['invited', 'quoted', 'quoted', 'declined', 'no_response']
                rfq_vendor = RFQVendor.objects.create(
                    rfq=rfq,
                    vendor=vendor,
                    status=random.choice(vendor_statuses),
                    responded_at=timezone.now() - timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None,
                )
                rfq_vendor_objs.append(rfq_vendor)

            # Create quotes for vendors that quoted
            for rfq_vendor in rfq_vendor_objs:
                if rfq_vendor.status == 'quoted':
                    for rfq_item in rfq_items:
                        base_price = rfq_item.item.unit_price if rfq_item.item else Decimal('10.00')
                        variation = Decimal(str(random.uniform(0.8, 1.3)))
                        unit_price = (base_price * variation).quantize(Decimal('0.01'))
                        VendorQuote.objects.create(
                            rfq_vendor=rfq_vendor,
                            rfq_item=rfq_item,
                            unit_price=unit_price,
                            total_price=unit_price * rfq_item.quantity,
                            lead_time_days=random.randint(3, 30),
                            notes=fake.sentence() if random.random() > 0.6 else '',
                            is_selected=False,
                        )

            rfqs.append(rfq)

        self.stdout.write(f'  Created {len(rfqs)} RFQs with vendor quotes')
        return rfqs

    def _create_purchase_orders(self, tenant, users, items, vendors, rfqs, requisitions):
        statuses = [
            'draft', 'pending_approval', 'approved', 'approved', 'sent',
            'acknowledged', 'partially_received', 'received', 'cancelled',
        ]
        approved_prs = [pr for pr in requisitions if pr.status == 'approved']

        purchase_orders = []
        for i in range(12):
            vendor = random.choice(vendors)
            status = random.choice(statuses)
            linked_rfq = random.choice(rfqs) if rfqs and random.random() > 0.5 else None
            linked_pr = random.choice(approved_prs) if approved_prs and random.random() > 0.5 else None

            po = PurchaseOrder(
                tenant=tenant,
                po_number=f'PO-{i + 1:05d}',
                vendor=vendor,
                rfq=linked_rfq,
                requisition=linked_pr,
                status=status,
                order_date=timezone.now().date() - timedelta(days=random.randint(1, 60)),
                expected_delivery_date=timezone.now().date() + timedelta(days=random.randint(7, 45)),
                payment_terms=vendor.payment_terms,
                shipping_address=fake.address(),
                notes=fake.sentence() if random.random() > 0.5 else '',
                created_by=random.choice(users),
            )
            if status in ('approved', 'sent', 'acknowledged', 'partially_received', 'received'):
                po.approved_by = random.choice(users)
                po.approved_at = timezone.now() - timedelta(days=random.randint(1, 15))
            po.save()

            # Add 2-5 line items
            selected_items = random.sample(items, k=random.randint(2, 5))
            subtotal = Decimal('0')
            for item in selected_items:
                qty = Decimal(str(random.randint(2, 50)))
                price = item.unit_price
                tax_rate = Decimal(str(random.choice([0, 5, 10, 15])))
                discount = Decimal(str(random.choice([0, 0, 0, 5, 10])))
                received_qty = Decimal('0')

                if status in ('partially_received',):
                    received_qty = qty * Decimal(str(random.uniform(0.3, 0.8))).quantize(Decimal('0.01'))
                elif status in ('received',):
                    received_qty = qty

                po_item = PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    item=item,
                    description=item.name,
                    quantity=qty,
                    unit_price=price,
                    tax_rate=tax_rate,
                    discount=discount,
                    received_quantity=received_qty,
                )
                subtotal += po_item.total_price

            po.subtotal = subtotal
            tax = subtotal * Decimal('0.05')
            po.tax_amount = tax.quantize(Decimal('0.01'))
            disc = Decimal(str(random.choice([0, 0, 10, 25, 50])))
            po.discount_amount = disc
            po.total_amount = (subtotal + po.tax_amount - disc).quantize(Decimal('0.01'))
            po.save(update_fields=['subtotal', 'tax_amount', 'discount_amount', 'total_amount'])

            purchase_orders.append(po)

        self.stdout.write(f'  Created {len(purchase_orders)} purchase orders')
        return purchase_orders

    def _create_grns(self, tenant, users, purchase_orders):
        eligible_pos = [
            po for po in purchase_orders
            if po.status in ('approved', 'sent', 'acknowledged', 'partially_received', 'received')
        ]

        grns = []
        for i, po in enumerate(eligible_pos[:8]):
            grn = GoodsReceiptNote(
                tenant=tenant,
                grn_number=f'GRN-{i + 1:05d}',
                purchase_order=po,
                received_by=random.choice(users),
                received_date=timezone.now().date() - timedelta(days=random.randint(0, 20)),
                status=random.choice(['draft', 'confirmed', 'confirmed', 'partial']),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            grn.save()

            # Add GRN items matching PO items
            for po_item in po.items.all():
                received = po_item.quantity if random.random() > 0.3 else po_item.quantity * Decimal('0.8')
                received = received.quantize(Decimal('0.01'))
                rejected = Decimal('0')
                if random.random() > 0.8:
                    rejected = (received * Decimal('0.1')).quantize(Decimal('0.01'))

                GRNItem.objects.create(
                    grn=grn,
                    po_item=po_item,
                    received_quantity=received,
                    accepted_quantity=received - rejected,
                    rejected_quantity=rejected,
                    rejection_reason='Minor defects found' if rejected > 0 else '',
                )

            grns.append(grn)

        self.stdout.write(f'  Created {len(grns)} goods receipt notes')
        return grns

    def _create_invoices(self, tenant, vendors, purchase_orders, grns):
        invoices = []
        eligible_pos = [
            po for po in purchase_orders
            if po.status in ('approved', 'sent', 'acknowledged', 'partially_received', 'received')
        ]

        for i, po in enumerate(eligible_pos[:8]):
            matching_grn = None
            for grn in grns:
                if grn.purchase_order_id == po.pk:
                    matching_grn = grn
                    break

            invoice = VendorInvoice(
                tenant=tenant,
                invoice_number=f'INV-{fake.bothify("####")}-{i + 1}',
                vendor=po.vendor,
                purchase_order=po,
                grn=matching_grn,
                invoice_date=timezone.now().date() - timedelta(days=random.randint(0, 15)),
                due_date=timezone.now().date() + timedelta(days=random.randint(15, 60)),
                subtotal=po.subtotal,
                tax_amount=po.tax_amount,
                total_amount=po.total_amount,
                status=random.choice(['pending', 'pending', 'matched', 'partially_matched', 'disputed', 'paid']),
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            invoice.save()

            # Add invoice items from PO items
            for po_item in po.items.all():
                VendorInvoiceItem.objects.create(
                    invoice=invoice,
                    po_item=po_item,
                    description=po_item.description or (po_item.item.name if po_item.item else ''),
                    quantity=po_item.quantity,
                    unit_price=po_item.unit_price,
                    total_price=po_item.total_price,
                )

            invoices.append(invoice)

        self.stdout.write(f'  Created {len(invoices)} vendor invoices')
        return invoices

    def _create_three_way_matches(self, tenant, purchase_orders, grns, invoices):
        count = 0
        for invoice in invoices:
            if invoice.purchase_order and invoice.grn:
                po = invoice.purchase_order
                grn = invoice.grn

                po_qty = sum(item.quantity for item in po.items.all())
                grn_qty = sum(item.accepted_quantity for item in grn.items.all())
                qty_match = abs(po_qty - grn_qty) < Decimal('0.01')
                price_match = abs(invoice.total_amount - po.total_amount) < Decimal('0.01')
                total_match = qty_match and price_match

                if total_match:
                    match_status = 'full_match'
                elif qty_match or price_match:
                    match_status = 'partial_match'
                else:
                    match_status = 'mismatch'

                ThreeWayMatch.objects.create(
                    tenant=tenant,
                    invoice=invoice,
                    purchase_order=po,
                    grn=grn,
                    match_status=match_status,
                    quantity_match=qty_match,
                    price_match=price_match,
                    total_match=total_match,
                    discrepancy_notes=fake.sentence() if match_status != 'full_match' else '',
                )
                count += 1

        self.stdout.write(f'  Created {count} three-way matches')

    def _create_shipment_updates(self, tenant, vendors, purchase_orders):
        eligible_pos = [
            po for po in purchase_orders
            if po.status in ('sent', 'acknowledged', 'partially_received', 'received')
        ]

        count = 0
        for po in eligible_pos:
            # Get a vendor contact for this vendor
            contact = VendorContact.objects.filter(tenant=tenant, vendor=po.vendor).first()

            statuses_sequence = ['preparing', 'shipped', 'in_transit', 'delivered']
            num_updates = random.randint(1, 4)

            for j in range(num_updates):
                ShipmentUpdate.objects.create(
                    purchase_order=po,
                    updated_by=contact,
                    status=statuses_sequence[min(j, 3)],
                    tracking_number=fake.bothify('??########') if j >= 1 else '',
                    carrier=random.choice(['FedEx', 'DHL', 'UPS', 'TNT', 'Aramex', 'Local Courier']),
                    estimated_arrival=timezone.now().date() + timedelta(days=random.randint(1, 10)),
                    notes=fake.sentence() if random.random() > 0.5 else '',
                )
                count += 1

        self.stdout.write(f'  Created {count} shipment updates')
