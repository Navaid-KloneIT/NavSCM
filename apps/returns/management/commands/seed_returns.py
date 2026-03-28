import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.oms.models import Customer, Order
from apps.procurement.models import Item, Vendor
from apps.returns.models import (
    Disposition,
    Refund,
    ReturnAuthorization,
    ReturnPortalSettings,
    RMALineItem,
    WarrantyClaim,
    WarrantyClaimItem,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample Returns Management data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing Returns data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing Returns data...'))
            WarrantyClaimItem.objects.all().delete()
            WarrantyClaim.objects.all().delete()
            Disposition.objects.all().delete()
            Refund.objects.all().delete()
            RMALineItem.objects.all().delete()
            ReturnAuthorization.objects.all().delete()
            ReturnPortalSettings.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All Returns data flushed.'))

        for tenant in tenants:
            self.stdout.write(f'\nSeeding Returns data for: {tenant.name}')
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

            customers = list(Customer.objects.filter(tenant=tenant, is_active=True))
            if not customers:
                self.stdout.write(self.style.WARNING(
                    '  No customers found. Run "python manage.py seed_oms" first.'
                ))
                continue

            vendors = list(Vendor.objects.filter(tenant=tenant, is_active=True))
            orders = list(Order.objects.filter(tenant=tenant))

            if ReturnAuthorization.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    '  Returns data already exists. Use --flush to re-seed.'
                ))
                continue

            # Portal Settings
            ReturnPortalSettings.objects.get_or_create(
                tenant=tenant,
                defaults={
                    'is_portal_enabled': True,
                    'return_window_days': 30,
                    'requires_approval': True,
                    'restocking_fee_percentage': Decimal('10.00'),
                    'return_policy_text': 'Items may be returned within 30 days of delivery.',
                },
            )
            self.stdout.write('  Created portal settings.')

            # RMAs
            rma_statuses = ['draft', 'submitted', 'approved', 'receiving', 'received', 'closed', 'rejected']
            rma_list = []
            now = timezone.now()

            for i in range(10):
                status = rma_statuses[i % len(rma_statuses)]
                customer = random.choice(customers)
                order = random.choice(orders) if orders else None

                rma = ReturnAuthorization(
                    tenant=tenant,
                    customer=customer,
                    order=order,
                    return_type=random.choice(['exchange', 'refund', 'repair', 'store_credit']),
                    reason_category=random.choice(['defective', 'wrong_item', 'damaged', 'not_as_described', 'changed_mind']),
                    status=status,
                    priority=random.choice(['low', 'medium', 'high', 'urgent']),
                    requested_date=(now - timedelta(days=random.randint(1, 60))).date(),
                    created_by=random.choice(users),
                    notes=f'Sample RMA #{i + 1} for testing.',
                )
                if status in ('approved', 'receiving', 'received', 'closed'):
                    rma.approved_by = random.choice(users)
                    rma.approved_date = (now - timedelta(days=random.randint(1, 30))).date()
                rma.save()
                rma_list.append(rma)

                # Line items
                for j in range(random.randint(1, 3)):
                    RMALineItem.objects.create(
                        rma=rma,
                        item=random.choice(items),
                        quantity=Decimal(str(random.randint(1, 10))),
                        reason=f'Return reason for item {j + 1}',
                        condition=random.choice(['new', 'used', 'damaged', 'defective']),
                    )

            self.stdout.write(f'  Created {len(rma_list)} RMAs with line items.')

            # Refunds - for approved/received/closed RMAs
            eligible_rmas = [r for r in rma_list if r.status in ('approved', 'received', 'closed')]
            refund_count = 0
            for rma in eligible_rmas[:6]:
                refund = Refund(
                    tenant=tenant,
                    rma=rma,
                    refund_type=random.choice(['full', 'partial', 'store_credit']),
                    refund_method=random.choice(['original_payment', 'bank_transfer', 'store_credit']),
                    amount=Decimal(str(random.randint(50, 500))),
                    currency='USD',
                    status=random.choice(['draft', 'pending_approval', 'approved', 'processing', 'completed']),
                    created_by=random.choice(users),
                    notes='Sample refund for testing.',
                )
                if refund.status == 'completed':
                    refund.processed_date = now.date()
                    refund.approved_by = random.choice(users)
                elif refund.status in ('approved', 'processing'):
                    refund.approved_by = random.choice(users)
                refund.save()
                refund_count += 1
            self.stdout.write(f'  Created {refund_count} refunds.')

            # Dispositions - for received/closed RMAs
            received_rmas = [r for r in rma_list if r.status in ('received', 'closed')]
            dsp_count = 0
            for rma in received_rmas[:5]:
                line_items_qs = rma.line_items.all()
                for li in line_items_qs[:2]:
                    dsp = Disposition(
                        tenant=tenant,
                        rma=rma,
                        rma_item=li,
                        item=li.item,
                        quantity=li.quantity,
                        condition_received=random.choice(['new', 'like_new', 'good', 'fair', 'poor', 'damaged']),
                        disposition_decision=random.choice(['restock', 'refurbish', 'repair', 'scrap', 'return_to_supplier']),
                        status=random.choice(['pending', 'inspecting', 'decided', 'processing', 'completed']),
                        assigned_to=random.choice(users),
                        inspection_notes='Inspected returned item.',
                        decision_notes='Disposition decision recorded.',
                        created_by=random.choice(users),
                    )
                    if dsp.status == 'completed':
                        dsp.completed_date = now.date()
                    dsp.save()
                    dsp_count += 1
            self.stdout.write(f'  Created {dsp_count} dispositions.')

            # Warranty Claims
            wc_count = 0
            if vendors:
                for i in range(5):
                    claim = WarrantyClaim(
                        tenant=tenant,
                        rma=random.choice(rma_list) if random.random() > 0.3 else None,
                        vendor=random.choice(vendors),
                        item=random.choice(items),
                        claim_type=random.choice(['manufacturer_warranty', 'supplier_warranty', 'extended_warranty']),
                        status=random.choice(['draft', 'submitted', 'under_review', 'approved', 'settled', 'denied', 'closed']),
                        warranty_start_date=(now - timedelta(days=random.randint(180, 365))).date(),
                        warranty_end_date=(now + timedelta(days=random.randint(30, 365))).date(),
                        claim_amount=Decimal(str(random.randint(100, 5000))),
                        settlement_amount=Decimal(str(random.randint(50, 3000))),
                        currency='USD',
                        description=f'Warranty claim #{i + 1} for defective item.',
                        resolution_notes='Claim resolution pending.' if i % 2 == 0 else '',
                        created_by=random.choice(users),
                    )
                    claim.save()

                    # Claim items
                    for j in range(random.randint(1, 3)):
                        qty = Decimal(str(random.randint(1, 5)))
                        unit_cost = Decimal(str(random.randint(10, 200)))
                        WarrantyClaimItem.objects.create(
                            claim=claim,
                            description=f'Defective component #{j + 1}',
                            quantity=qty,
                            unit_cost=unit_cost,
                            total=qty * unit_cost,
                        )
                    wc_count += 1
            self.stdout.write(f'  Created {wc_count} warranty claims with items.')

        self.stdout.write(self.style.SUCCESS('\nReturns Management seed complete!'))
        self.stdout.write(self.style.WARNING(
            '\nNote: Superuser "admin" has no tenant — data won\'t appear '
            'when logged in as admin. Use a tenant admin account (e.g., admin_<slug>).'
        ))
