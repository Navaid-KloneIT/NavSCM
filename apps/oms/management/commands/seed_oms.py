import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.inventory.models import Warehouse
from apps.oms.models import (
    AllocationItem,
    Backorder,
    Customer,
    CustomerNotification,
    Order,
    OrderAllocation,
    OrderItem,
    OrderValidation,
    SalesChannel,
)
from apps.procurement.models import Item

from faker import Faker

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake OMS data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing OMS data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing OMS data...'))
            CustomerNotification.objects.all().delete()
            Backorder.objects.all().delete()
            AllocationItem.objects.all().delete()
            OrderAllocation.objects.all().delete()
            OrderValidation.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            SalesChannel.objects.all().delete()
            Customer.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All OMS data flushed.'))

        tenant_admins = []

        for tenant in tenants:
            self.stdout.write(f'\nSeeding OMS data for: {tenant.name}')

            users = list(User.objects.filter(tenant=tenant, is_active=True))
            if not users:
                self.stdout.write(self.style.WARNING(f'  No users found, skipping.'))
                continue

            if Customer.objects.filter(tenant=tenant).exists() and not options['flush']:
                self.stdout.write(self.style.WARNING(
                    f'  OMS data already exists for tenant "{tenant.name}". Use --flush to re-seed.'
                ))
                continue

            items = list(Item.objects.filter(tenant=tenant, is_active=True))
            if not items:
                self.stdout.write(self.style.WARNING(
                    f'  No items found. Run "python manage.py seed_procurement" first.'
                ))
                continue

            warehouses = list(Warehouse.objects.filter(tenant=tenant, is_active=True))

            # Seed data
            customers = self._create_customers(tenant)
            channels = self._create_sales_channels(tenant)
            orders = self._create_orders(tenant, users, customers, channels, items)
            self._create_validations(tenant, users, orders)
            if warehouses:
                self._create_allocations(tenant, users, orders, items, warehouses)
            self._create_backorders(tenant, orders, items)
            self._create_notifications(tenant, orders, customers)

            admin_user = User.objects.filter(tenant=tenant, is_tenant_admin=True).first()
            if admin_user:
                tenant_admins.append(admin_user.username)

            self.stdout.write(self.style.SUCCESS(f'  Done seeding OMS for "{tenant.name}"'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('OMS seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('To see OMS data, log in as a tenant admin:')
        for username in tenant_admins:
            self.stdout.write(f'  Username: {username} / Password: password123')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: The superuser "admin" has no tenant, so OMS data '
            'will NOT appear when logged in as admin.'
        ))

    def _create_customers(self, tenant):
        self.stdout.write('  Creating customers...')
        customers = []
        for i in range(15):
            number = f'CUST-{i + 1:05d}'
            existing = Customer.objects.filter(tenant=tenant, customer_number=number).first()
            if existing:
                customers.append(existing)
                continue

            customer = Customer.objects.create(
                tenant=tenant,
                customer_number=number,
                name=fake.company(),
                email=fake.company_email(),
                phone=fake.phone_number()[:20],
                company=fake.company(),
                billing_address=fake.address(),
                shipping_address=fake.address(),
                credit_limit=Decimal(str(random.randint(5000, 100000))),
                is_active=random.choice([True, True, True, False]),
            )
            customers.append(customer)
        self.stdout.write(f'    Created {len(customers)} customers')
        return customers

    def _create_sales_channels(self, tenant):
        self.stdout.write('  Creating sales channels...')
        channel_data = [
            ('Website Store', 'website'),
            ('Amazon Marketplace', 'marketplace'),
            ('eBay Marketplace', 'marketplace'),
            ('Phone Orders', 'phone'),
            ('EDI Integration', 'edi'),
            ('Manual Entry', 'manual'),
        ]
        channels = []
        for name, ch_type in channel_data:
            channel, _ = SalesChannel.objects.get_or_create(
                tenant=tenant,
                name=name,
                defaults={
                    'channel_type': ch_type,
                    'is_active': True,
                },
            )
            channels.append(channel)
        self.stdout.write(f'    Created {len(channels)} sales channels')
        return channels

    def _create_orders(self, tenant, users, customers, channels, items):
        self.stdout.write('  Creating orders...')
        orders = []
        statuses = ['draft', 'pending_validation', 'validated', 'allocated',
                     'in_fulfillment', 'partially_shipped', 'shipped',
                     'delivered', 'cancelled', 'on_hold']
        priorities = ['low', 'medium', 'medium', 'high', 'urgent']

        for i in range(20):
            number = f'ORD-{i + 1:05d}'
            existing = Order.objects.filter(tenant=tenant, order_number=number).first()
            if existing:
                orders.append(existing)
                continue

            status = random.choice(statuses)
            customer = random.choice(customers)
            order_date = timezone.now().date() - timedelta(days=random.randint(0, 60))

            order = Order(
                tenant=tenant,
                order_number=number,
                customer=customer,
                sales_channel=random.choice(channels),
                status=status,
                priority=random.choice(priorities),
                order_date=order_date,
                required_date=order_date + timedelta(days=random.randint(5, 30)),
                shipping_address=customer.shipping_address,
                billing_address=customer.billing_address,
                notes=fake.sentence() if random.random() > 0.5 else '',
                created_by=random.choice(users),
            )

            if status in ('validated', 'allocated', 'in_fulfillment',
                          'partially_shipped', 'shipped', 'delivered'):
                order.validated_by = random.choice(users)
                order.validated_at = timezone.now() - timedelta(days=random.randint(1, 30))

            order.save()

            # Add 2-5 line items
            subtotal = Decimal('0')
            selected_items = random.sample(items, k=min(random.randint(2, 5), len(items)))
            for item in selected_items:
                qty = Decimal(str(random.randint(1, 20)))
                price = item.unit_price if hasattr(item, 'unit_price') and item.unit_price else Decimal(str(random.randint(10, 500)))
                tax = (qty * price * Decimal('0.05')).quantize(Decimal('0.01'))
                discount = Decimal(str(random.choice([0, 0, 5, 10]))).quantize(Decimal('0.01'))
                total = (qty * price + tax - discount).quantize(Decimal('0.01'))

                oi_status = 'pending'
                allocated_qty = Decimal('0')
                shipped_qty = Decimal('0')
                if status in ('allocated', 'in_fulfillment'):
                    oi_status = 'allocated'
                    allocated_qty = qty
                elif status in ('partially_shipped',):
                    oi_status = random.choice(['allocated', 'partially_shipped'])
                    allocated_qty = qty
                    if oi_status == 'partially_shipped':
                        shipped_qty = (qty * Decimal('0.5')).quantize(Decimal('0.01'))
                elif status in ('shipped', 'delivered'):
                    oi_status = 'shipped'
                    allocated_qty = qty
                    shipped_qty = qty
                elif status == 'cancelled':
                    oi_status = 'cancelled'

                OrderItem.objects.create(
                    order=order,
                    item=item,
                    quantity=qty,
                    unit_price=price,
                    tax_amount=tax,
                    discount_amount=discount,
                    total_price=total,
                    allocated_quantity=allocated_qty,
                    shipped_quantity=shipped_qty,
                    status=oi_status,
                )
                subtotal += total

            # Update order totals
            shipping = Decimal(str(random.choice([0, 10, 15, 25, 50]))).quantize(Decimal('0.01'))
            order.subtotal = subtotal
            order.tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
            order.discount_amount = Decimal(str(random.choice([0, 0, 10, 25]))).quantize(Decimal('0.01'))
            order.shipping_amount = shipping
            order.total_amount = (subtotal + shipping).quantize(Decimal('0.01'))
            order.save(update_fields=['subtotal', 'tax_amount', 'discount_amount',
                                      'shipping_amount', 'total_amount'])
            orders.append(order)

        self.stdout.write(f'    Created {len(orders)} orders')
        return orders

    def _create_validations(self, tenant, users, orders):
        self.stdout.write('  Creating order validations...')
        count = 0
        validation_types = ['credit_check', 'inventory_check', 'fraud_check', 'address_verification']

        for order in orders:
            if order.status in ('draft',):
                continue

            for i, v_type in enumerate(random.sample(validation_types, k=random.randint(1, 3))):
                number = f'OV-{count + 1:05d}'
                existing = OrderValidation.objects.filter(
                    tenant=tenant, validation_number=number
                ).first()
                if existing:
                    count += 1
                    continue

                if order.status in ('pending_validation',):
                    v_status = random.choice(['pending', 'passed'])
                elif order.status == 'cancelled':
                    v_status = random.choice(['passed', 'failed'])
                else:
                    v_status = 'passed'

                validation = OrderValidation(
                    tenant=tenant,
                    order=order,
                    validation_number=number,
                    validation_type=v_type,
                    status=v_status,
                    result_notes=fake.sentence() if v_status != 'pending' else '',
                )
                if v_status != 'pending':
                    validation.validated_by = random.choice(users)
                    validation.validated_at = timezone.now() - timedelta(days=random.randint(1, 20))
                validation.save()
                count += 1

        self.stdout.write(f'    Created {count} validations')

    def _create_allocations(self, tenant, users, orders, items, warehouses):
        self.stdout.write('  Creating order allocations...')
        count = 0

        for order in orders:
            if order.status not in ('allocated', 'in_fulfillment', 'partially_shipped',
                                     'shipped', 'delivered'):
                continue

            number = f'ALLOC-{count + 1:05d}'
            existing = OrderAllocation.objects.filter(
                tenant=tenant, allocation_number=number
            ).first()
            if existing:
                count += 1
                continue

            warehouse = random.choice(warehouses)
            methods = ['nearest', 'lowest_cost', 'highest_stock', 'manual']

            allocation = OrderAllocation.objects.create(
                tenant=tenant,
                order=order,
                allocation_number=number,
                warehouse=warehouse,
                allocation_method=random.choice(methods),
                status='allocated',
                allocated_by=random.choice(users),
                allocated_at=timezone.now() - timedelta(days=random.randint(1, 15)),
                notes=fake.sentence() if random.random() > 0.6 else '',
            )

            # Create allocation items for each order item
            for oi in order.items.all():
                AllocationItem.objects.create(
                    allocation=allocation,
                    order_item=oi,
                    item=oi.item,
                    requested_quantity=oi.quantity,
                    allocated_quantity=oi.allocated_quantity,
                    warehouse=warehouse,
                )

            count += 1

        self.stdout.write(f'    Created {count} allocations')

    def _create_backorders(self, tenant, orders, items):
        self.stdout.write('  Creating backorders...')
        count = 0
        statuses = ['pending', 'pending', 'partially_fulfilled', 'fulfilled', 'cancelled']

        for order in orders[:8]:
            if order.status in ('draft', 'cancelled', 'delivered'):
                continue

            order_items = list(order.items.all())
            if not order_items:
                continue

            oi = random.choice(order_items)
            number = f'BO-{count + 1:05d}'
            existing = Backorder.objects.filter(
                tenant=tenant, backorder_number=number
            ).first()
            if existing:
                count += 1
                continue

            bo_status = random.choice(statuses)
            qty = (oi.quantity * Decimal('0.3')).quantize(Decimal('0.01'))
            fulfilled_qty = Decimal('0')
            if bo_status == 'partially_fulfilled':
                fulfilled_qty = (qty * Decimal('0.5')).quantize(Decimal('0.01'))
            elif bo_status == 'fulfilled':
                fulfilled_qty = qty

            Backorder.objects.create(
                tenant=tenant,
                backorder_number=number,
                order=order,
                order_item=oi,
                item=oi.item,
                quantity=qty,
                fulfilled_quantity=fulfilled_qty,
                status=bo_status,
                expected_date=timezone.now().date() + timedelta(days=random.randint(7, 45)) if bo_status == 'pending' else None,
                notes=fake.sentence() if random.random() > 0.5 else '',
            )
            count += 1

        self.stdout.write(f'    Created {count} backorders')

    def _create_notifications(self, tenant, orders, customers):
        self.stdout.write('  Creating customer notifications...')
        count = 0
        notification_types = [
            'order_confirmation', 'order_validated', 'order_shipped',
            'order_delivered', 'backorder_alert', 'order_cancelled',
        ]
        channels = ['email', 'sms', 'both']
        n_statuses = ['pending', 'sent', 'sent', 'delivered', 'failed']

        for order in orders:
            if order.status == 'draft':
                continue

            # 1-3 notifications per order
            for _ in range(random.randint(1, 3)):
                number = f'CN-{count + 1:05d}'
                existing = CustomerNotification.objects.filter(
                    tenant=tenant, notification_number=number
                ).first()
                if existing:
                    count += 1
                    continue

                n_type = random.choice(notification_types)
                n_status = random.choice(n_statuses)

                subjects = {
                    'order_confirmation': f'Order {order.order_number} Confirmed',
                    'order_validated': f'Order {order.order_number} Validated',
                    'order_shipped': f'Order {order.order_number} Shipped',
                    'order_delivered': f'Order {order.order_number} Delivered',
                    'backorder_alert': f'Backorder Alert for {order.order_number}',
                    'order_cancelled': f'Order {order.order_number} Cancelled',
                }

                notification = CustomerNotification(
                    tenant=tenant,
                    notification_number=number,
                    order=order,
                    customer=order.customer,
                    notification_type=n_type,
                    channel=random.choice(channels),
                    status=n_status,
                    subject=subjects.get(n_type, f'Order {order.order_number} Update'),
                    message=fake.paragraph(),
                )
                if n_status in ('sent', 'delivered'):
                    notification.sent_at = timezone.now() - timedelta(days=random.randint(0, 15))
                notification.save()
                count += 1

        self.stdout.write(f'    Created {count} notifications')
