import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.oms.models import Customer, Order
from apps.procurement.models import Item
from apps.tms.models import Shipment
from apps.portal.models import (
    CatalogItem,
    OrderTracking,
    PortalAccount,
    PortalDocument,
    SupportTicket,
    TicketMessage,
    TrackingEvent,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample Customer Portal data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing portal data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing portal data...')
            TrackingEvent.objects.all().delete()
            TicketMessage.objects.all().delete()
            OrderTracking.objects.all().delete()
            SupportTicket.objects.all().delete()
            PortalDocument.objects.all().delete()
            CatalogItem.objects.all().delete()
            PortalAccount.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Portal data flushed.'))

        for tenant in tenants:
            if PortalAccount.objects.filter(tenant=tenant).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Portal data already exists for {tenant.name}. Use --flush to re-seed.'
                    )
                )
                continue

            self.stdout.write(f'Seeding portal data for {tenant.name}...')
            users = list(User.objects.filter(tenant=tenant, is_active=True))
            customers = list(Customer.objects.filter(tenant=tenant, is_active=True))
            orders = list(Order.objects.filter(tenant=tenant))
            shipments = list(Shipment.objects.filter(tenant=tenant))
            items = list(Item.objects.filter(tenant=tenant, is_active=True))

            if not users or not customers:
                self.stdout.write(self.style.WARNING(
                    f'  No users or customers for {tenant.name}. Skipping.'
                ))
                continue

            admin_user = users[0]
            now = timezone.now()

            # -----------------------------------------------------------------
            # Portal Accounts
            # -----------------------------------------------------------------
            account_statuses = ['active', 'active', 'active', 'pending', 'suspended']
            payment_methods = ['credit_card', 'bank_transfer', 'paypal', 'cod']
            languages = ['en', 'en', 'en', 'es', 'fr', 'ar']

            accounts = []
            for customer in customers[:8]:
                account = PortalAccount.objects.create(
                    tenant=tenant,
                    customer=customer,
                    display_name=customer.name,
                    portal_email=customer.email or f'{customer.name.lower().replace(" ", ".")}@example.com',
                    phone=customer.phone or '',
                    status=random.choice(account_statuses),
                    preferred_language=random.choice(languages),
                    billing_address=customer.billing_address or '123 Business St',
                    shipping_address=customer.shipping_address or '456 Warehouse Ave',
                    payment_method=random.choice(payment_methods),
                    payment_reference=f'REF-{random.randint(10000, 99999)}',
                    created_by=admin_user,
                )
                accounts.append(account)

            self.stdout.write(f'  Created {len(accounts)} portal accounts.')

            # -----------------------------------------------------------------
            # Order Trackings
            # -----------------------------------------------------------------
            tracking_statuses = ['processing', 'shipped', 'in_transit', 'delivered', 'delayed']
            locations = [
                'Main Warehouse', 'Distribution Hub A', 'Regional Center',
                'Local Depot', 'In Transit - Highway', 'Customer City',
            ]
            carriers = ['FedEx', 'UPS', 'DHL', 'Aramex', 'Local Courier']

            trackings = []
            for i in range(min(12, len(orders))):
                order = orders[i] if i < len(orders) else random.choice(orders)
                status = random.choice(tracking_statuses)
                account = random.choice(accounts)

                tracking = OrderTracking.objects.create(
                    tenant=tenant,
                    portal_account=account,
                    order=order,
                    shipment=random.choice(shipments) if shipments else None,
                    current_status=status,
                    estimated_delivery=(now + timedelta(days=random.randint(1, 14))).date(),
                    actual_delivery=(now - timedelta(days=random.randint(0, 3))).date() if status == 'delivered' else None,
                    last_location=random.choice(locations),
                    carrier_name=random.choice(carriers),
                    carrier_tracking_url='',
                    created_by=admin_user,
                )
                trackings.append(tracking)

                # Add tracking events
                event_statuses = ['processing', 'shipped', 'in_transit']
                if status in ('delivered',):
                    event_statuses.append('out_for_delivery')
                    event_statuses.append('delivered')
                for j, evt_status in enumerate(event_statuses):
                    TrackingEvent.objects.create(
                        tracking=tracking,
                        event_date=now - timedelta(days=len(event_statuses) - j),
                        location=random.choice(locations),
                        status=evt_status,
                        description=f'Package {evt_status.replace("_", " ")}.',
                    )

            self.stdout.write(f'  Created {len(trackings)} order trackings.')

            # -----------------------------------------------------------------
            # Portal Documents
            # -----------------------------------------------------------------
            doc_types = ['invoice', 'proof_of_delivery', 'contract', 'packing_list', 'credit_note']
            doc_statuses = ['draft', 'published', 'published', 'published', 'archived']

            documents = []
            for i in range(10):
                doc_type = random.choice(doc_types)
                account = random.choice(accounts)

                doc = PortalDocument.objects.create(
                    tenant=tenant,
                    portal_account=account,
                    document_type=doc_type,
                    title=f'{doc_type.replace("_", " ").title()} - {account.display_name}',
                    reference_number=f'REF-{random.randint(10000, 99999)}',
                    order=random.choice(orders) if orders else None,
                    file_path=f'/documents/{doc_type}_{i + 1}.pdf',
                    file_size=random.randint(10240, 5242880),
                    status=random.choice(doc_statuses),
                    issue_date=(now - timedelta(days=random.randint(1, 60))).date(),
                    expiry_date=(now + timedelta(days=random.randint(30, 365))).date() if doc_type == 'contract' else None,
                    uploaded_by=admin_user,
                )
                documents.append(doc)

            self.stdout.write(f'  Created {len(documents)} portal documents.')

            # -----------------------------------------------------------------
            # Support Tickets
            # -----------------------------------------------------------------
            categories = ['order_issue', 'delivery_issue', 'billing', 'product_inquiry', 'return_request', 'general']
            priorities = ['low', 'medium', 'medium', 'high', 'urgent']
            ticket_statuses = ['open', 'in_progress', 'resolved', 'closed', 'waiting_on_customer']
            subjects = [
                'Missing items in order', 'Delivery delayed', 'Invoice discrepancy',
                'Product availability inquiry', 'Return request for damaged goods',
                'Account access issue', 'Billing address update', 'Order cancellation request',
                'Quality concern', 'Shipping cost inquiry',
            ]

            tickets = []
            for i in range(10):
                account = random.choice(accounts)
                status = random.choice(ticket_statuses)

                ticket = SupportTicket.objects.create(
                    tenant=tenant,
                    portal_account=account,
                    order=random.choice(orders) if orders and random.choice([True, False]) else None,
                    subject=random.choice(subjects),
                    category=random.choice(categories),
                    priority=random.choice(priorities),
                    status=status,
                    description=f'Sample support ticket for {account.display_name}. This requires attention.',
                    assigned_to=random.choice(users) if status != 'open' else None,
                    resolved_at=now - timedelta(hours=random.randint(1, 48)) if status in ('resolved', 'closed') else None,
                    resolution_notes='Issue has been resolved.' if status in ('resolved', 'closed') else '',
                    created_by=admin_user,
                )
                tickets.append(ticket)

                # Add messages
                msg_count = random.randint(1, 4)
                sender_types = ['customer', 'agent', 'system']
                for j in range(msg_count):
                    TicketMessage.objects.create(
                        ticket=ticket,
                        sender_name=account.display_name if j % 2 == 0 else 'Support Agent',
                        sender_type='customer' if j % 2 == 0 else random.choice(['agent', 'system']),
                        message=f'Message #{j + 1} regarding the ticket.',
                    )

            self.stdout.write(f'  Created {len(tickets)} support tickets.')

            # -----------------------------------------------------------------
            # Catalog Items
            # -----------------------------------------------------------------
            stock_statuses = ['in_stock', 'in_stock', 'in_stock', 'low_stock', 'out_of_stock', 'pre_order']
            categories_list = ['Electronics', 'Raw Materials', 'Packaging', 'Tools', 'Safety Equipment', 'Office Supplies']

            catalog_items = []
            for item in items[:12]:
                cat_item = CatalogItem.objects.create(
                    tenant=tenant,
                    item=item,
                    portal_name=item.name,
                    portal_description=f'High-quality {item.name} available for order.',
                    category=random.choice(categories_list),
                    unit_price=Decimal(str(random.randint(5, 500))) + Decimal('0.99'),
                    currency='USD',
                    stock_status=random.choice(stock_statuses),
                    available_quantity=random.randint(0, 1000),
                    minimum_order_quantity=random.choice([1, 5, 10, 25]),
                    lead_time_days=random.randint(1, 14),
                    is_featured=random.choice([True, False, False]),
                    is_active=random.choice([True, True, True, False]),
                    created_by=admin_user,
                )
                catalog_items.append(cat_item)

            self.stdout.write(f'  Created {len(catalog_items)} catalog items.')

        self.stdout.write(self.style.SUCCESS('\nCustomer Portal data seeded successfully!'))
        self.stdout.write(self.style.WARNING(
            '\nNote: Superuser "admin" has no tenant — data won\'t appear when logged in as admin.'
        ))
        self.stdout.write('Log in as a tenant admin (e.g., admin_<tenant-slug>) to see portal data.')
