import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.inventory.models import Warehouse
from apps.labor.models import (
    Attendance,
    LaborPlan,
    LaborPlanLine,
    PayrollRecord,
    PerformanceReview,
    TaskAssignment,
    TaskChecklistItem,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample Labor Management data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing labor data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing labor data...')
            TaskChecklistItem.objects.all().delete()
            LaborPlanLine.objects.all().delete()
            TaskAssignment.objects.all().delete()
            Attendance.objects.all().delete()
            PerformanceReview.objects.all().delete()
            PayrollRecord.objects.all().delete()
            LaborPlan.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Labor data flushed.'))

        for tenant in tenants:
            if LaborPlan.objects.filter(tenant=tenant).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Labor data already exists for {tenant.name}. Use --flush to re-seed.'
                    )
                )
                continue

            self.stdout.write(f'Seeding labor data for {tenant.name}...')
            users = list(User.objects.filter(tenant=tenant, is_active=True))
            warehouses = list(Warehouse.objects.filter(tenant=tenant, is_active=True))

            if not users:
                self.stdout.write(self.style.WARNING(f'  No users found for {tenant.name}. Skipping.'))
                continue

            admin_user = users[0]
            now = timezone.now()

            # -----------------------------------------------------------------
            # Labor Plans
            # -----------------------------------------------------------------
            departments = ['receiving', 'picking', 'packing', 'shipping', 'loading', 'general']
            shifts = ['morning', 'afternoon', 'night']
            roles = ['Picker', 'Packer', 'Forklift Operator', 'Supervisor', 'Loader', 'Receiving Clerk']
            plan_statuses = ['draft', 'approved', 'active', 'completed']

            plans = []
            for i in range(10):
                plan = LaborPlan.objects.create(
                    tenant=tenant,
                    title=f'{random.choice(departments).title()} Staffing Plan - Week {i + 1}',
                    warehouse=random.choice(warehouses) if warehouses else None,
                    department=random.choice(departments),
                    shift=random.choice(shifts),
                    plan_date=(now + timedelta(days=i * 7)).date(),
                    status=random.choice(plan_statuses),
                    expected_inbound_volume=random.randint(100, 2000),
                    expected_outbound_volume=random.randint(100, 2000),
                    required_headcount=random.randint(5, 30),
                    available_headcount=random.randint(3, 25),
                    notes=f'Sample labor plan #{i + 1} for {tenant.name}.',
                    created_by=admin_user,
                )
                plans.append(plan)

                # Add plan lines
                for role in random.sample(roles, random.randint(2, 4)):
                    LaborPlanLine.objects.create(
                        plan=plan,
                        role=role,
                        required_count=random.randint(1, 8),
                        available_count=random.randint(0, 6),
                        hourly_rate=Decimal(str(random.randint(12, 35))),
                        notes='',
                    )

            self.stdout.write(f'  Created {len(plans)} labor plans.')

            # -----------------------------------------------------------------
            # Attendance Records
            # -----------------------------------------------------------------
            att_statuses = ['clocked_in', 'clocked_out', 'approved', 'locked']
            records = []
            for i in range(20):
                day_offset = random.randint(0, 30)
                record_date = (now - timedelta(days=day_offset)).date()
                hour = random.choice([6, 14, 22])
                clock_in_time = now.replace(
                    year=record_date.year, month=record_date.month,
                    day=record_date.day, hour=hour, minute=0, second=0,
                    microsecond=0,
                )
                clock_out_time = clock_in_time + timedelta(hours=random.randint(7, 10))
                status = random.choice(att_statuses)

                record = Attendance.objects.create(
                    tenant=tenant,
                    worker=random.choice(users),
                    warehouse=random.choice(warehouses) if warehouses else None,
                    date=record_date,
                    status=status,
                    shift=random.choice(shifts),
                    clock_in=clock_in_time,
                    clock_out=clock_out_time if status != 'clocked_in' else None,
                    break_duration_minutes=random.choice([0, 15, 30, 45, 60]),
                    overtime_hours=Decimal(str(random.choice([0, 0.5, 1, 1.5, 2]))),
                    standard_hours_per_day=Decimal('8.00'),
                    notes='',
                    created_by=admin_user,
                )
                records.append(record)

            self.stdout.write(f'  Created {len(records)} attendance records.')

            # -----------------------------------------------------------------
            # Task Assignments
            # -----------------------------------------------------------------
            task_types = ['picking', 'packing', 'receiving', 'loading', 'putaway', 'counting']
            priorities = ['low', 'medium', 'high', 'urgent']
            task_statuses = ['pending', 'assigned', 'in_progress', 'completed']
            checklist_items_options = [
                'Verify SKU counts', 'Check item condition', 'Scan barcodes',
                'Update inventory system', 'Confirm pallet placement',
                'Verify shipping labels', 'Check weight', 'Record lot numbers',
            ]

            tasks = []
            for i in range(15):
                task_type = random.choice(task_types)
                status = random.choice(task_statuses)
                started = now - timedelta(hours=random.randint(1, 48)) if status in ('in_progress', 'completed') else None
                completed = started + timedelta(hours=random.randint(1, 4)) if status == 'completed' and started else None
                units = random.randint(20, 500)

                task = TaskAssignment.objects.create(
                    tenant=tenant,
                    title=f'{task_type.title()} Order #{random.randint(1000, 9999)}',
                    task_type=task_type,
                    priority=random.choice(priorities),
                    status=status,
                    warehouse=random.choice(warehouses) if warehouses else None,
                    assigned_to=random.choice(users) if status != 'pending' else None,
                    assigned_date=(now - timedelta(days=random.randint(0, 7))).date() if status != 'pending' else None,
                    due_date=(now + timedelta(days=random.randint(0, 5))).date(),
                    started_at=started,
                    completed_at=completed,
                    estimated_duration_minutes=random.randint(30, 240),
                    actual_duration_minutes=random.randint(30, 240) if status == 'completed' else 0,
                    units_to_process=units,
                    units_processed=units if status == 'completed' else random.randint(0, units),
                    errors_count=random.randint(0, 5) if status == 'completed' else 0,
                    description=f'Sample {task_type} task for {tenant.name}.',
                    notes='',
                    created_by=admin_user,
                )
                tasks.append(task)

                # Add checklist items
                for item in random.sample(checklist_items_options, random.randint(2, 4)):
                    TaskChecklistItem.objects.create(
                        task=task,
                        item_name=item,
                        is_completed=random.choice([True, False]) if status in ('in_progress', 'completed') else False,
                    )

            self.stdout.write(f'  Created {len(tasks)} task assignments.')

            # -----------------------------------------------------------------
            # Performance Reviews
            # -----------------------------------------------------------------
            ratings = ['exceptional', 'exceeds_expectations', 'meets_expectations', 'needs_improvement']
            review_statuses = ['draft', 'submitted', 'approved', 'closed']

            reviews = []
            for i in range(8):
                period_start = (now - timedelta(days=30 * (i + 1))).date()
                period_end = (now - timedelta(days=30 * i)).date()

                review = PerformanceReview.objects.create(
                    tenant=tenant,
                    worker=random.choice(users),
                    warehouse=random.choice(warehouses) if warehouses else None,
                    period_start=period_start,
                    period_end=period_end,
                    status=random.choice(review_statuses),
                    tasks_completed=random.randint(10, 100),
                    total_units_processed=random.randint(500, 5000),
                    total_hours_worked=Decimal(str(random.randint(120, 200))),
                    total_errors=random.randint(0, 20),
                    rating=random.choice(ratings),
                    reviewer_comments='Performance tracked over the review period.',
                    reviewed_by=admin_user,
                    created_by=admin_user,
                )
                reviews.append(review)

            self.stdout.write(f'  Created {len(reviews)} performance reviews.')

            # -----------------------------------------------------------------
            # Payroll Records
            # -----------------------------------------------------------------
            payroll_statuses = ['draft', 'calculated', 'approved', 'exported']

            payrolls = []
            for i in range(10):
                period_start = (now - timedelta(days=14 * (i + 1))).date()
                period_end = (now - timedelta(days=14 * i)).date()
                regular = Decimal(str(random.randint(70, 90)))
                overtime = Decimal(str(random.randint(0, 20)))
                rate = Decimal(str(random.randint(15, 40)))
                ot_rate = round(rate * Decimal('1.5'), 2)

                payroll = PayrollRecord.objects.create(
                    tenant=tenant,
                    worker=random.choice(users),
                    period_start=period_start,
                    period_end=period_end,
                    status=random.choice(payroll_statuses),
                    regular_hours=regular,
                    overtime_hours=overtime,
                    hourly_rate=rate,
                    overtime_rate=ot_rate,
                    deductions=Decimal(str(random.randint(50, 200))),
                    bonuses=Decimal(str(random.choice([0, 50, 100, 150]))),
                    currency='USD',
                    days_worked=random.randint(8, 14),
                    days_absent=random.randint(0, 3),
                    notes='',
                    exported_at=now if random.choice([True, False]) else None,
                    created_by=admin_user,
                )
                payrolls.append(payroll)

            self.stdout.write(f'  Created {len(payrolls)} payroll records.')

        self.stdout.write(self.style.SUCCESS('\nLabor Management data seeded successfully!'))
        self.stdout.write(self.style.WARNING(
            '\nNote: Superuser "admin" has no tenant — data won\'t appear when logged in as admin.'
        ))
        self.stdout.write('Log in as a tenant admin (e.g., admin_<tenant-slug>) to see labor data.')
