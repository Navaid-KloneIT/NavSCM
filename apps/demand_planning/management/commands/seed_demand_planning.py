import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.demand_planning.models import (
    CollaborativePlan,
    DemandSignal,
    ForecastLineItem,
    PlanComment,
    PlanLineItem,
    PromotionalEvent,
    SafetyStockCalculation,
    SafetyStockItem,
    SalesForecast,
    SeasonalityProfile,
)
from apps.inventory.models import Warehouse
from apps.procurement.models import Item


class Command(BaseCommand):
    help = 'Seed the database with sample demand planning data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing demand planning data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing demand planning data...'))
            SafetyStockItem.objects.all().delete()
            SafetyStockCalculation.objects.all().delete()
            PlanComment.objects.all().delete()
            PlanLineItem.objects.all().delete()
            CollaborativePlan.objects.all().delete()
            DemandSignal.objects.all().delete()
            PromotionalEvent.objects.all().delete()
            ForecastLineItem.objects.all().delete()
            SalesForecast.objects.all().delete()
            SeasonalityProfile.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All demand planning data flushed.'))

        for tenant in tenants:
            self.stdout.write(f'\nSeeding demand planning data for: {tenant.name}')
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

            warehouses = list(Warehouse.objects.filter(tenant=tenant, is_active=True))
            if not warehouses:
                self.stdout.write(self.style.WARNING(
                    '  No warehouses found. Run "python manage.py seed_inventory" first.'
                ))
                continue

            if SalesForecast.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    '  Demand planning data already exists. Use --flush to re-seed.'
                ))
                continue

            self._create_seasonality_profiles(tenant, users, items)
            self._create_promotional_events(tenant, users)
            self._create_sales_forecasts(tenant, users, items)
            self._create_demand_signals(tenant, users, items)
            self._create_collaborative_plans(tenant, users, items)
            self._create_safety_stock_calculations(tenant, users, items, warehouses)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Demand planning seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Log in as a tenant admin (e.g., admin_<slug>) to see module data.'
        ))
        self.stdout.write(self.style.WARNING(
            'Superuser "admin" has no tenant — data will not appear.'
        ))

    def _create_seasonality_profiles(self, tenant, users, items):
        profiles_data = [
            {
                'name': 'Winter Goods Seasonal Pattern',
                'factors': {
                    'jan': 1.40, 'feb': 1.30, 'mar': 1.00, 'apr': 0.70,
                    'may': 0.50, 'jun': 0.40, 'jul': 0.40, 'aug': 0.50,
                    'sep': 0.80, 'oct': 1.10, 'nov': 1.50, 'dec': 1.80,
                },
            },
            {
                'name': 'Summer Products Pattern',
                'factors': {
                    'jan': 0.50, 'feb': 0.60, 'mar': 0.80, 'apr': 1.10,
                    'may': 1.40, 'jun': 1.70, 'jul': 1.80, 'aug': 1.60,
                    'sep': 1.20, 'oct': 0.80, 'nov': 0.50, 'dec': 0.40,
                },
            },
            {
                'name': 'Office Supplies Seasonal Pattern',
                'factors': {
                    'jan': 1.30, 'feb': 1.10, 'mar': 1.00, 'apr': 0.90,
                    'may': 0.85, 'jun': 0.80, 'jul': 0.70, 'aug': 1.20,
                    'sep': 1.40, 'oct': 1.10, 'nov': 1.00, 'dec': 0.80,
                },
            },
            {
                'name': 'Steady Demand Pattern',
                'factors': {
                    'jan': 1.00, 'feb': 1.00, 'mar': 1.05, 'apr': 1.05,
                    'may': 1.00, 'jun': 0.95, 'jul': 0.95, 'aug': 1.00,
                    'sep': 1.05, 'oct': 1.05, 'nov': 1.00, 'dec': 0.95,
                },
            },
        ]

        sample_items = items[:min(len(items), len(profiles_data))]
        count = 0
        for i, data in enumerate(profiles_data):
            if i >= len(sample_items):
                break
            item = sample_items[i]
            profile, created = SeasonalityProfile.objects.get_or_create(
                tenant=tenant,
                item=item,
                defaults={
                    'name': data['name'],
                    'description': f"Seasonal demand pattern for {item.name}",
                    'jan_factor': data['factors']['jan'],
                    'feb_factor': data['factors']['feb'],
                    'mar_factor': data['factors']['mar'],
                    'apr_factor': data['factors']['apr'],
                    'may_factor': data['factors']['may'],
                    'jun_factor': data['factors']['jun'],
                    'jul_factor': data['factors']['jul'],
                    'aug_factor': data['factors']['aug'],
                    'sep_factor': data['factors']['sep'],
                    'oct_factor': data['factors']['oct'],
                    'nov_factor': data['factors']['nov'],
                    'dec_factor': data['factors']['dec'],
                    'is_active': True,
                    'created_by': random.choice(users),
                },
            )
            if created:
                count += 1
        self.stdout.write(f'  Created {count} seasonality profiles')

    def _create_promotional_events(self, tenant, users):
        profiles = list(SeasonalityProfile.objects.filter(tenant=tenant))
        events_data = [
            ('Black Friday Sale', 'promotion', 11, 25, 11, 30, Decimal('2.00')),
            ('Holiday Season', 'holiday', 12, 15, 12, 31, Decimal('1.80')),
            ('Summer Clearance', 'clearance', 7, 1, 7, 31, Decimal('1.50')),
            ('New Year Launch', 'launch', 1, 5, 1, 20, Decimal('1.40')),
            ('Spring Sale', 'seasonal', 3, 15, 4, 15, Decimal('1.30')),
            ('Back to School', 'promotion', 8, 10, 9, 10, Decimal('1.60')),
        ]

        now = timezone.now()
        count = 0
        for name, etype, sm, sd, em, ed, impact in events_data:
            start = now.replace(month=sm, day=sd).date()
            end = now.replace(month=em, day=ed).date()
            profile = random.choice(profiles) if profiles else None
            event, created = PromotionalEvent.objects.get_or_create(
                tenant=tenant,
                name=name,
                defaults={
                    'description': f'{name} promotional event',
                    'event_type': etype,
                    'seasonality_profile': profile,
                    'start_date': start,
                    'end_date': end,
                    'impact_factor': impact,
                    'is_active': True,
                    'created_by': random.choice(users),
                },
            )
            if created:
                count += 1
        self.stdout.write(f'  Created {count} promotional events')

    def _create_sales_forecasts(self, tenant, users, items):
        now = timezone.now()
        forecasts_data = [
            ('Q1 2026 Sales Forecast', 'moving_average', 'active', 1, 3),
            ('Q2 2026 Sales Forecast', 'exponential_smoothing', 'approved', 4, 6),
            ('Q3 2026 Demand Projection', 'linear_regression', 'submitted', 7, 9),
            ('Q4 2026 Holiday Forecast', 'manual', 'draft', 10, 12),
            ('Annual 2026 Overview', 'moving_average', 'archived', 1, 12),
            ('FY2027 Planning Forecast', 'exponential_smoothing', 'draft', 1, 12),
        ]

        count = 0
        for title, method, status, sm, em in forecasts_data:
            start = now.replace(month=sm, day=1).date()
            end = now.replace(month=em, day=28).date()
            user = random.choice(users)

            forecast = SalesForecast(
                tenant=tenant,
                title=title,
                description=f'Forecast for {title}',
                forecast_method=method,
                start_date=start,
                end_date=end,
                status=status,
                created_by=user,
            )
            if status in ('approved', 'active', 'archived'):
                forecast.approved_by = random.choice(users)
                forecast.approved_at = now - timedelta(days=random.randint(5, 30))
            forecast.save()

            sample_items = random.sample(items, min(len(items), random.randint(3, 6)))
            for item in sample_items:
                forecasted = Decimal(str(random.randint(100, 5000)))
                actual = None
                if status in ('active', 'archived'):
                    variance = Decimal(str(random.randint(-20, 20))) / 100
                    actual = (forecasted * (1 + variance)).quantize(Decimal('0.01'))
                ForecastLineItem.objects.create(
                    forecast=forecast,
                    item=item,
                    forecasted_quantity=forecasted,
                    actual_quantity=actual,
                    confidence_level=Decimal(str(random.randint(60, 98))),
                    notes=f'Forecast for {item.name}',
                )
            count += 1
        self.stdout.write(f'  Created {count} sales forecasts with line items')

    def _create_demand_signals(self, tenant, users, items):
        now = timezone.now()
        signals_data = [
            ('Rising commodity prices', 'economic_indicator', 'high', 15.0, 'analyzed'),
            ('Competitor product recall', 'competitor_action', 'critical', 30.0, 'incorporated'),
            ('Social media trending product', 'social_media', 'medium', 20.0, 'new'),
            ('Severe weather forecast', 'weather', 'high', -10.0, 'analyzed'),
            ('POS data spike in northeast', 'pos_data', 'medium', 12.0, 'new'),
            ('Customer survey results', 'customer_feedback', 'low', 5.0, 'dismissed'),
            ('New market trend: sustainability', 'market_trend', 'medium', 8.0, 'new'),
            ('Economic downturn indicators', 'economic_indicator', 'high', -15.0, 'analyzed'),
            ('Competitor clearance sale', 'competitor_action', 'medium', -8.0, 'new'),
            ('Viral product review online', 'social_media', 'high', 25.0, 'incorporated'),
        ]

        count = 0
        for title, stype, impact, pct, status in signals_data:
            user = random.choice(users)
            signal = DemandSignal(
                tenant=tenant,
                title=title,
                description=f'Signal: {title}',
                signal_type=stype,
                impact_level=impact,
                status=status,
                item=random.choice(items) if random.random() > 0.3 else None,
                estimated_impact_pct=Decimal(str(pct)),
                signal_date=(now - timedelta(days=random.randint(1, 60))).date(),
                expiry_date=(now + timedelta(days=random.randint(30, 180))).date() if random.random() > 0.5 else None,
                source=random.choice([
                    'Market Intelligence Team', 'Sales Report', 'Industry News',
                    'Social Media Monitor', 'Customer Survey', 'POS Analytics',
                ]),
                created_by=user,
            )
            if status in ('analyzed', 'incorporated'):
                signal.analyzed_by = random.choice(users)
                signal.analyzed_at = now - timedelta(days=random.randint(1, 10))
            signal.save()
            count += 1
        self.stdout.write(f'  Created {count} demand signals')

    def _create_collaborative_plans(self, tenant, users, items):
        now = timezone.now()
        forecasts = list(SalesForecast.objects.filter(tenant=tenant))
        plans_data = [
            ('Q2 2026 Sales Plan', 'sales_plan', 'finalized', 4, 6),
            ('Summer Marketing Campaign Plan', 'marketing_plan', 'approved', 5, 8),
            ('H2 2026 Finance Budget Plan', 'finance_plan', 'submitted', 7, 12),
            ('Q3 Operations Alignment', 'operations_plan', 'draft', 7, 9),
            ('Annual Consensus Forecast', 'consensus', 'review', 1, 12),
        ]

        count = 0
        for title, ptype, status, sm, em in plans_data:
            start = now.replace(month=sm, day=1).date()
            end = now.replace(month=em, day=28).date()
            user = random.choice(users)

            plan = CollaborativePlan(
                tenant=tenant,
                title=title,
                description=f'Collaborative plan: {title}',
                plan_type=ptype,
                status=status,
                start_date=start,
                end_date=end,
                forecast=random.choice(forecasts) if forecasts and random.random() > 0.3 else None,
                created_by=user,
            )
            if status in ('approved', 'finalized'):
                plan.approved_by = random.choice(users)
                plan.approved_at = now - timedelta(days=random.randint(3, 20))
            plan.save()

            sample_items = random.sample(items, min(len(items), random.randint(3, 5)))
            for item in sample_items:
                PlanLineItem.objects.create(
                    plan=plan,
                    item=item,
                    planned_quantity=Decimal(str(random.randint(200, 8000))),
                    notes=f'Planned quantity for {item.name}',
                )

            comments_text = [
                'Looks good, aligning with our Q3 targets.',
                'We should revisit the numbers for the northeast region.',
                'Marketing campaign will drive extra demand — factor in 15% uplift.',
                'Finance approved the budget for this plan.',
                'Recommend increasing safety stock for key items.',
            ]
            for text in random.sample(comments_text, min(len(comments_text), random.randint(2, 4))):
                PlanComment.objects.create(
                    plan=plan,
                    author=random.choice(users),
                    content=text,
                )
            count += 1
        self.stdout.write(f'  Created {count} collaborative plans with line items and comments')

    def _create_safety_stock_calculations(self, tenant, users, items, warehouses):
        now = timezone.now()
        calcs_data = [
            ('Q1 2026 Safety Stock Review', 'statistical', 'applied', Decimal('95.00')),
            ('Q2 2026 Buffer Calculation', 'demand_based', 'approved', Decimal('97.50')),
            ('Mid-Year Stock Assessment', 'percentage', 'calculated', Decimal('95.00')),
            ('Q4 2026 Pre-Holiday Buffer', 'statistical', 'draft', Decimal('99.00')),
        ]

        count = 0
        for title, method, status, service_level in calcs_data:
            user = random.choice(users)
            calc = SafetyStockCalculation(
                tenant=tenant,
                title=title,
                description=f'Safety stock calculation: {title}',
                calculation_method=method,
                status=status,
                calculation_date=(now - timedelta(days=random.randint(5, 60))).date(),
                default_service_level=service_level,
                created_by=user,
            )
            if status in ('approved', 'applied'):
                calc.approved_by = random.choice(users)
                calc.approved_at = now - timedelta(days=random.randint(1, 15))
            calc.save()

            sample_items = random.sample(items, min(len(items), random.randint(3, 6)))
            for item in sample_items:
                wh = random.choice(warehouses)
                avg_demand = Decimal(str(random.randint(20, 200)))
                std_dev = (avg_demand * Decimal(str(random.randint(10, 40))) / 100).quantize(Decimal('0.01'))
                lt_days = random.randint(3, 21)
                lt_std = Decimal(str(random.randint(1, 5)))
                current = Decimal(str(random.randint(50, 500)))

                ss_item = SafetyStockItem(
                    calculation=calc,
                    item=item,
                    warehouse=wh,
                    avg_demand=avg_demand,
                    demand_std_dev=std_dev,
                    lead_time_days=lt_days,
                    lead_time_std_dev=lt_std,
                    service_level_pct=service_level,
                    current_stock=current,
                )

                if status in ('calculated', 'approved', 'applied'):
                    import math
                    z_scores = {
                        Decimal('90.00'): Decimal('1.28'),
                        Decimal('95.00'): Decimal('1.65'),
                        Decimal('97.50'): Decimal('1.96'),
                        Decimal('99.00'): Decimal('2.33'),
                    }
                    z = z_scores.get(service_level, Decimal('1.65'))
                    lt = Decimal(str(lt_days))
                    under_root = (lt * std_dev * std_dev) + (avg_demand * avg_demand * lt_std * lt_std)
                    safety = z * Decimal(str(math.sqrt(float(under_root))))
                    ss_item.calculated_safety_stock = safety.quantize(Decimal('0.01'))
                    ss_item.recommended_reorder_point = (
                        (avg_demand * lt) + ss_item.calculated_safety_stock
                    ).quantize(Decimal('0.01'))

                ss_item.save()
            count += 1
        self.stdout.write(f'  Created {count} safety stock calculations with items')
