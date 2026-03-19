"""
Management command to seed the database with fake data for development.

Usage:
    python manage.py seed_data
    python manage.py seed_data --tenants 3 --users 20
    python manage.py seed_data --flush  (clears all data first)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.core.models import Tenant, Subscription, AuditLog
from apps.accounts.models import User, Role, UserInvite

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenants',
            type=int,
            default=3,
            help='Number of tenants to create (default: 3)',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=15,
            help='Number of users per tenant (default: 15)',
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing data before seeding',
        )

    def handle(self, *args, **options):
        num_tenants = options['tenants']
        num_users = options['users']

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing existing data...'))
            AuditLog.objects.all().delete()
            UserInvite.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Role.objects.all().delete()
            Subscription.objects.all().delete()
            Tenant.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All data flushed.'))

        # Create superuser if not exists
        if not User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.create_superuser(
                username='admin',
                email='admin@navhcm.com',
                password='admin123',
                first_name='Super',
                last_name='Admin',
            )
            self.stdout.write(self.style.SUCCESS(
                f'Superuser created: admin / admin123'
            ))

        # Define default roles per tenant
        default_roles = [
            {
                'name': 'Admin',
                'slug': 'admin',
                'description': 'Full administrative access',
                'is_system_role': True,
                'permissions': [
                    'manage_users', 'manage_roles', 'manage_settings',
                    'view_audit_logs', 'manage_subscriptions',
                ],
            },
            {
                'name': 'HR Manager',
                'slug': 'hr-manager',
                'description': 'Human resource management access',
                'is_system_role': True,
                'permissions': [
                    'manage_users', 'view_reports', 'manage_attendance',
                    'manage_leave', 'manage_payroll',
                ],
            },
            {
                'name': 'Manager',
                'slug': 'manager',
                'description': 'Department manager access',
                'is_system_role': False,
                'permissions': [
                    'view_team', 'approve_leave', 'view_reports',
                    'manage_attendance',
                ],
            },
            {
                'name': 'Employee',
                'slug': 'employee',
                'description': 'Standard employee access',
                'is_system_role': False,
                'permissions': [
                    'view_profile', 'apply_leave', 'view_attendance',
                    'view_payslip',
                ],
            },
            {
                'name': 'Viewer',
                'slug': 'viewer',
                'description': 'Read-only access',
                'is_system_role': False,
                'permissions': ['view_profile', 'view_attendance'],
            },
        ]

        departments = [
            'Engineering', 'Human Resources', 'Finance', 'Marketing',
            'Sales', 'Operations', 'Product', 'Design', 'Legal',
            'Customer Support',
        ]

        job_titles = [
            'Software Engineer', 'Senior Developer', 'Product Manager',
            'HR Specialist', 'Financial Analyst', 'Marketing Manager',
            'Sales Executive', 'Operations Lead', 'UX Designer',
            'Legal Counsel', 'Support Specialist', 'Data Analyst',
            'DevOps Engineer', 'QA Engineer', 'Business Analyst',
        ]

        plan_choices = ['free', 'starter', 'professional', 'enterprise']

        for t_idx in range(num_tenants):
            company_name = fake.company()
            slug = fake.slug() + f'-{t_idx}'

            tenant, created = Tenant.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': company_name,
                    'domain': f'{slug}.navhcm.com',
                    'is_active': True,
                },
            )

            if created:
                self.stdout.write(f'  Created tenant: {tenant.name}')
            else:
                self.stdout.write(f'  Tenant already exists: {tenant.name}')
                continue

            # Create subscription
            plan = plan_choices[t_idx % len(plan_choices)]
            max_users_map = {
                'free': 5, 'starter': 25,
                'professional': 100, 'enterprise': 500,
            }
            Subscription.objects.create(
                tenant=tenant,
                plan=plan,
                status='active',
                max_users=max_users_map[plan],
                max_storage_gb=10 * (plan_choices.index(plan) + 1),
                start_date=timezone.now().date(),
            )
            self.stdout.write(f'    Subscription: {plan} plan')

            # Create roles
            tenant_roles = []
            for role_data in default_roles:
                role, _ = Role.objects.get_or_create(
                    tenant=tenant,
                    slug=role_data['slug'],
                    defaults={
                        'name': role_data['name'],
                        'description': role_data['description'],
                        'is_system_role': role_data['is_system_role'],
                        'permissions': role_data['permissions'],
                    },
                )
                tenant_roles.append(role)

            self.stdout.write(f'    Created {len(default_roles)} roles')

            # Create tenant admin user
            admin_user = User.objects.create_user(
                username=f'admin_{slug}',
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                tenant=tenant,
                role=tenant_roles[0],  # Admin role
                is_tenant_admin=True,
                phone=fake.phone_number()[:20],
                job_title='Chief Executive Officer',
                department='Executive',
                bio=fake.paragraph(nb_sentences=3),
            )
            self.stdout.write(f'    Admin user: {admin_user.username} / password123')

            # Create regular users
            for u_idx in range(num_users - 1):
                role = fake.random_element(tenant_roles[1:])  # Non-admin roles
                dept = fake.random_element(departments)
                title = fake.random_element(job_titles)

                user = User.objects.create_user(
                    username=fake.user_name() + f'_{t_idx}_{u_idx}',
                    email=fake.email(),
                    password='password123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    tenant=tenant,
                    role=role,
                    is_active=fake.boolean(chance_of_getting_true=90),
                    phone=fake.phone_number()[:20],
                    job_title=title,
                    department=dept,
                    bio=fake.paragraph(nb_sentences=2) if fake.boolean() else '',
                )

            self.stdout.write(f'    Created {num_users} users total')

            # Create some user invites
            invite_statuses = ['pending', 'pending', 'pending', 'accepted', 'expired']
            for _ in range(5):
                status = fake.random_element(invite_statuses)
                invite = UserInvite.objects.create(
                    tenant=tenant,
                    email=fake.email(),
                    role=fake.random_element(tenant_roles),
                    invited_by=admin_user,
                    status=status,
                    message=fake.sentence() if fake.boolean() else '',
                )

            self.stdout.write(f'    Created 5 user invites')

            # Create some audit log entries
            actions = [
                'user.login', 'user.logout', 'user.create', 'user.update',
                'role.create', 'settings.update', 'invite.send', 'profile.update',
            ]
            models = ['User', 'Role', 'Tenant', 'UserInvite', 'Subscription']
            for _ in range(20):
                AuditLog.objects.create(
                    tenant=tenant,
                    user=fake.random_element(
                        User.objects.filter(tenant=tenant)
                    ),
                    action=fake.random_element(actions),
                    model_name=fake.random_element(models),
                    object_id=str(fake.random_int(min=1, max=100)),
                    changes={
                        'field': fake.word(),
                        'old': fake.word(),
                        'new': fake.word(),
                    },
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                )

            self.stdout.write(f'    Created 20 audit log entries')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write(f'  Superadmin: admin / admin123')
        self.stdout.write(f'  Tenant admins: admin_<slug> / password123')
        self.stdout.write(f'  All other users: password123')
        self.stdout.write('')
