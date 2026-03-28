import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.inventory.models import Warehouse
from apps.procurement.models import Item, Vendor
from apps.tms.models import Carrier
from apps.analytics.models import (
    FinancialReport,
    FinancialReportItem,
    InventoryAnalytics,
    InventoryAnalyticsItem,
    LogisticsKPI,
    LogisticsKPIItem,
    PredictiveAlert,
    ProcurementAnalytics,
    ProcurementAnalyticsItem,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample Supply Chain Analytics data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing Analytics data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing Analytics data...'))
            PredictiveAlert.objects.all().delete()
            FinancialReportItem.objects.all().delete()
            FinancialReport.objects.all().delete()
            LogisticsKPIItem.objects.all().delete()
            LogisticsKPI.objects.all().delete()
            ProcurementAnalyticsItem.objects.all().delete()
            ProcurementAnalytics.objects.all().delete()
            InventoryAnalyticsItem.objects.all().delete()
            InventoryAnalytics.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All Analytics data flushed.'))

        for tenant in tenants:
            self.stdout.write(f'\nSeeding Analytics data for: {tenant.name}')
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

            if InventoryAnalytics.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    '  Analytics data already exists. Use --flush to re-seed.'
                ))
                continue

            warehouses = list(Warehouse.objects.filter(tenant=tenant))
            vendors = list(Vendor.objects.filter(tenant=tenant, is_active=True))
            carriers = list(Carrier.objects.filter(tenant=tenant))
            now = timezone.now()

            # --- Inventory Analytics ---
            inv_statuses = ['draft', 'generated', 'reviewed', 'archived']
            inv_types = ['turnover_analysis', 'dead_stock', 'aging_inventory', 'stock_summary']
            for i in range(8):
                report = InventoryAnalytics(
                    tenant=tenant,
                    report_type=inv_types[i % len(inv_types)],
                    status=inv_statuses[i % len(inv_statuses)],
                    start_date=(now - timedelta(days=90 + i * 30)).date(),
                    end_date=(now - timedelta(days=i * 30)).date(),
                    total_items=random.randint(50, 500),
                    total_value=Decimal(str(random.randint(10000, 500000))),
                    turnover_rate=Decimal(str(round(random.uniform(1.0, 12.0), 2))),
                    dead_stock_count=random.randint(0, 50),
                    dead_stock_value=Decimal(str(random.randint(0, 50000))),
                    aging_30_count=random.randint(10, 100),
                    aging_60_count=random.randint(5, 50),
                    aging_90_count=random.randint(2, 30),
                    aging_90_plus_count=random.randint(0, 20),
                    created_by=random.choice(users),
                )
                report.save()
                if warehouses and items:
                    for _ in range(random.randint(3, 6)):
                        InventoryAnalyticsItem.objects.create(
                            report=report,
                            item=random.choice(items),
                            warehouse=random.choice(warehouses),
                            quantity_on_hand=Decimal(str(random.randint(10, 500))),
                            quantity_reserved=Decimal(str(random.randint(0, 50))),
                            unit_cost=Decimal(str(round(random.uniform(5, 200), 2))),
                            total_value=Decimal(str(random.randint(500, 50000))),
                            days_since_last_movement=random.randint(0, 180),
                            turnover_rate=Decimal(str(round(random.uniform(0.5, 15.0), 2))),
                            is_dead_stock=random.random() < 0.15,
                        )
            self.stdout.write('  Created 8 inventory analytics reports.')

            # --- Procurement Analytics ---
            prc_types = ['spend_analysis', 'vendor_performance', 'cost_savings', 'purchase_summary']
            for i in range(8):
                report = ProcurementAnalytics(
                    tenant=tenant,
                    report_type=prc_types[i % len(prc_types)],
                    status=inv_statuses[i % len(inv_statuses)],
                    start_date=(now - timedelta(days=90 + i * 30)).date(),
                    end_date=(now - timedelta(days=i * 30)).date(),
                    total_spend=Decimal(str(random.randint(50000, 1000000))),
                    total_orders=random.randint(20, 200),
                    avg_order_value=Decimal(str(random.randint(500, 10000))),
                    on_time_delivery_rate=Decimal(str(round(random.uniform(70, 99), 2))),
                    rejection_rate=Decimal(str(round(random.uniform(0.5, 10), 2))),
                    top_vendor_spend=Decimal(str(random.randint(10000, 200000))),
                    created_by=random.choice(users),
                )
                report.save()
                if vendors:
                    for _ in range(random.randint(3, 6)):
                        ProcurementAnalyticsItem.objects.create(
                            report=report,
                            vendor=random.choice(vendors),
                            total_spend=Decimal(str(random.randint(5000, 100000))),
                            order_count=random.randint(5, 50),
                            avg_lead_time_days=Decimal(str(round(random.uniform(3, 30), 2))),
                            on_time_rate=Decimal(str(round(random.uniform(60, 100), 2))),
                            rejection_rate=Decimal(str(round(random.uniform(0, 15), 2))),
                            cost_variance=Decimal(str(round(random.uniform(-5000, 5000), 2))),
                        )
            self.stdout.write('  Created 8 procurement analytics reports.')

            # --- Logistics KPIs ---
            log_types = ['delivery_performance', 'freight_cost', 'vehicle_utilization', 'carrier_performance']
            for i in range(8):
                total_ship = random.randint(50, 500)
                on_time = int(total_ship * random.uniform(0.7, 0.98))
                late = total_ship - on_time
                report = LogisticsKPI(
                    tenant=tenant,
                    report_type=log_types[i % len(log_types)],
                    status=inv_statuses[i % len(inv_statuses)],
                    start_date=(now - timedelta(days=90 + i * 30)).date(),
                    end_date=(now - timedelta(days=i * 30)).date(),
                    total_shipments=total_ship,
                    on_time_count=on_time,
                    late_count=late,
                    on_time_rate=Decimal(str(round(on_time / total_ship * 100, 2))),
                    total_freight_cost=Decimal(str(random.randint(10000, 200000))),
                    avg_cost_per_shipment=Decimal(str(round(random.uniform(100, 1000), 2))),
                    avg_transit_days=Decimal(str(round(random.uniform(2, 14), 2))),
                    vehicle_utilization_rate=Decimal(str(round(random.uniform(50, 95), 2))),
                    created_by=random.choice(users),
                )
                report.save()
                if carriers:
                    for _ in range(random.randint(2, 5)):
                        c_ship = random.randint(10, 100)
                        c_on = int(c_ship * random.uniform(0.6, 1.0))
                        LogisticsKPIItem.objects.create(
                            report=report,
                            carrier=random.choice(carriers),
                            shipment_count=c_ship,
                            on_time_count=c_on,
                            late_count=c_ship - c_on,
                            on_time_rate=Decimal(str(round(c_on / c_ship * 100, 2))),
                            total_cost=Decimal(str(random.randint(5000, 50000))),
                            avg_cost_per_shipment=Decimal(str(round(random.uniform(100, 800), 2))),
                            avg_transit_days=Decimal(str(round(random.uniform(1, 10), 2))),
                        )
            self.stdout.write('  Created 8 logistics KPI reports.')

            # --- Financial Reports ---
            fin_types = ['gross_margin', 'cost_breakdown', 'revenue_analysis', 'profitability']
            cost_categories = [
                'Raw Materials', 'Labor', 'Transportation', 'Warehousing',
                'Packaging', 'Overhead', 'Quality Control', 'Insurance',
            ]
            for i in range(8):
                revenue = Decimal(str(random.randint(200000, 2000000)))
                cogs = revenue * Decimal(str(round(random.uniform(0.4, 0.7), 2)))
                margin = revenue - cogs
                report = FinancialReport(
                    tenant=tenant,
                    report_type=fin_types[i % len(fin_types)],
                    status=inv_statuses[i % len(inv_statuses)],
                    start_date=(now - timedelta(days=90 + i * 30)).date(),
                    end_date=(now - timedelta(days=i * 30)).date(),
                    total_revenue=revenue,
                    total_cogs=cogs,
                    gross_margin=margin,
                    gross_margin_percentage=Decimal(str(round(float(margin / revenue * 100), 2))),
                    procurement_cost=Decimal(str(random.randint(20000, 200000))),
                    logistics_cost=Decimal(str(random.randint(10000, 100000))),
                    manufacturing_cost=Decimal(str(random.randint(30000, 300000))),
                    warehousing_cost=Decimal(str(random.randint(5000, 50000))),
                    created_by=random.choice(users),
                )
                report.save()
                total_amount = float(cogs)
                for cat in random.sample(cost_categories, random.randint(3, 6)):
                    amt = Decimal(str(round(random.uniform(5000, 100000), 2)))
                    FinancialReportItem.objects.create(
                        report=report,
                        category=cat,
                        description=f'{cat} costs for the period',
                        amount=amt,
                        percentage_of_total=Decimal(str(round(float(amt) / total_amount * 100, 2))) if total_amount else Decimal('0'),
                    )
            self.stdout.write('  Created 8 financial reports.')

            # --- Predictive Alerts ---
            alert_types = ['demand_spike', 'supply_disruption', 'stockout_risk', 'price_fluctuation', 'delivery_delay']
            alert_statuses = ['new', 'analyzing', 'confirmed', 'resolved', 'dismissed']
            severities = ['low', 'medium', 'high', 'critical']
            for i in range(10):
                alert = PredictiveAlert(
                    tenant=tenant,
                    title=f'Sample Alert #{i + 1}: {random.choice(alert_types).replace("_", " ").title()}',
                    alert_type=random.choice(alert_types),
                    severity=random.choice(severities),
                    status=alert_statuses[i % len(alert_statuses)],
                    description=f'Automated prediction alert for testing purposes.',
                    affected_item=random.choice(items) if random.random() > 0.3 else None,
                    affected_vendor=random.choice(vendors) if vendors and random.random() > 0.5 else None,
                    predicted_date=(now + timedelta(days=random.randint(1, 60))).date(),
                    confidence_level=Decimal(str(round(random.uniform(40, 98), 2))),
                    impact_description='Potential impact on supply chain operations.',
                    recommended_action='Monitor closely and prepare contingency plan.',
                    created_by=random.choice(users),
                )
                if alert.status == 'resolved':
                    alert.resolved_by = random.choice(users)
                    alert.resolved_date = now.date()
                    alert.resolution_notes = 'Alert resolved after investigation.'
                alert.save()
            self.stdout.write('  Created 10 predictive alerts.')

        self.stdout.write(self.style.SUCCESS('\nSupply Chain Analytics seed complete!'))
        self.stdout.write(self.style.WARNING(
            '\nNote: Superuser "admin" has no tenant — data won\'t appear '
            'when logged in as admin. Use a tenant admin account (e.g., admin_<slug>).'
        ))
