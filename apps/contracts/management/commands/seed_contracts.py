import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contracts.models import (
    ComplianceCheckItem,
    ComplianceRecord,
    Contract,
    ContractDocument,
    License,
    SustainabilityMetric,
    SustainabilityReport,
    TradeDocument,
    TradeDocumentItem,
)
from apps.core.models import Tenant
from apps.procurement.models import Vendor

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample Contract & Compliance Management data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete existing contracts data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing contracts data...')
            SustainabilityMetric.objects.all().delete()
            SustainabilityReport.objects.all().delete()
            License.objects.all().delete()
            TradeDocumentItem.objects.all().delete()
            TradeDocument.objects.all().delete()
            ComplianceCheckItem.objects.all().delete()
            ComplianceRecord.objects.all().delete()
            ContractDocument.objects.all().delete()
            Contract.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Flushed.'))

        today = timezone.now().date()

        for tenant in tenants:
            self.stdout.write(f'\nSeeding contracts data for tenant: {tenant.name}')

            users = list(User.objects.filter(tenant=tenant, is_active=True)[:5])
            vendors = list(Vendor.objects.filter(tenant=tenant, is_active=True)[:5])

            if not users:
                self.stdout.write(self.style.WARNING(f'  No users for {tenant.name}. Skipping.'))
                continue

            if Contract.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    f'  Data already exists for {tenant.name}. Use --flush to re-seed.'
                ))
                continue

            # -----------------------------------------------------------------
            # 1. Contracts
            # -----------------------------------------------------------------
            contract_types = ['logistics', 'supplier_agreement', 'nda', 'service_agreement', 'lease', 'purchase_agreement']
            contract_statuses = ['draft', 'active', 'active', 'active', 'under_review', 'expired', 'terminated']
            contracts_created = []

            for i in range(8):
                c = Contract(
                    tenant=tenant,
                    title=f'Contract {i + 1} - {random.choice(["Logistics Agreement", "Supplier Terms", "NDA", "Service SLA", "Warehouse Lease", "Purchase Agreement"])}',
                    contract_type=random.choice(contract_types),
                    vendor=random.choice(vendors) if vendors else None,
                    status=contract_statuses[i % len(contract_statuses)],
                    start_date=today - timedelta(days=random.randint(30, 365)),
                    end_date=today + timedelta(days=random.randint(30, 730)),
                    value=random.randint(5000, 500000),
                    currency=random.choice(['USD', 'EUR', 'GBP', 'PKR']),
                    description=f'Sample contract #{i + 1} for {tenant.name}.',
                    terms_and_conditions='Standard terms and conditions apply.',
                    auto_renew=random.choice([True, False]),
                    renewal_period_days=random.choice([0, 30, 90, 365]),
                    notice_period_days=random.choice([15, 30, 60]),
                    created_by=random.choice(users),
                )
                c.save()
                contracts_created.append(c)

                # Add 1-2 documents per contract
                for j in range(random.randint(1, 2)):
                    ContractDocument.objects.create(
                        contract=c,
                        document_name=f'Document {j + 1} - {random.choice(["Signed Copy", "Amendment", "Addendum", "Terms Sheet"])}',
                        description=f'Attachment for {c.contract_number}',
                        file_reference=f'/docs/{c.contract_number}/{j + 1}.pdf',
                    )

            self.stdout.write(f'  Created {len(contracts_created)} contracts with documents.')

            # -----------------------------------------------------------------
            # 2. Compliance Records
            # -----------------------------------------------------------------
            regulations = [
                ('FDA Food Safety Compliance', 'fda'),
                ('HazMat Transportation Regulations', 'hazmat'),
                ('GDPR Data Protection', 'gdpr'),
                ('ISO 9001 Quality Management', 'iso'),
                ('Customs Import Regulations', 'customs'),
                ('Environmental Protection Act', 'environmental'),
                ('Trade Sanctions Compliance', 'trade_sanctions'),
            ]
            compliance_statuses = ['draft', 'in_compliance', 'in_compliance', 'non_compliant', 'under_review', 'expired']
            risk_levels = ['low', 'medium', 'high', 'critical']
            check_results = ['pass', 'pass', 'pass', 'fail', 'pending', 'na']
            records_created = []

            for i, (reg_name, reg_type) in enumerate(regulations):
                r = ComplianceRecord(
                    tenant=tenant,
                    regulation_name=reg_name,
                    regulation_type=reg_type,
                    status=compliance_statuses[i % len(compliance_statuses)],
                    compliance_date=today - timedelta(days=random.randint(10, 180)),
                    expiry_date=today + timedelta(days=random.randint(30, 365)),
                    responsible_person=random.choice(users),
                    description=f'{reg_name} compliance tracking for {tenant.name}.',
                    corrective_action='Review and update procedures as needed.' if i % 3 == 0 else '',
                    risk_level=random.choice(risk_levels),
                    created_by=random.choice(users),
                )
                r.save()
                records_created.append(r)

                # Add 2-4 check items
                check_items_list = [
                    'Documentation review', 'Process audit', 'Employee training verification',
                    'Equipment calibration check', 'Record keeping compliance', 'Reporting timeliness',
                ]
                for ci_name in random.sample(check_items_list, random.randint(2, 4)):
                    ComplianceCheckItem.objects.create(
                        compliance_record=r,
                        check_item=ci_name,
                        result=random.choice(check_results),
                        notes=f'Checked on {today}' if random.random() > 0.5 else '',
                    )

            self.stdout.write(f'  Created {len(records_created)} compliance records with check items.')

            # -----------------------------------------------------------------
            # 3. Trade Documents
            # -----------------------------------------------------------------
            doc_types = ['bill_of_lading', 'commercial_invoice', 'packing_list', 'certificate_of_origin', 'customs_declaration', 'letter_of_credit']
            doc_statuses = ['draft', 'issued', 'issued', 'in_transit', 'delivered', 'archived']
            countries = ['United States', 'China', 'Germany', 'United Kingdom', 'Pakistan', 'UAE', 'India', 'Japan']
            docs_created = []

            for i in range(8):
                td = TradeDocument(
                    tenant=tenant,
                    document_type=doc_types[i % len(doc_types)],
                    status=doc_statuses[i % len(doc_statuses)],
                    vendor=random.choice(vendors) if vendors else None,
                    origin_country=random.choice(countries),
                    destination_country=random.choice(countries),
                    issue_date=today - timedelta(days=random.randint(5, 60)),
                    reference_number=f'REF-{random.randint(10000, 99999)}',
                    value=random.randint(1000, 100000),
                    currency=random.choice(['USD', 'EUR', 'GBP']),
                    description=f'Trade document for international shipment #{i + 1}.',
                    created_by=random.choice(users),
                )
                td.save()
                docs_created.append(td)

                # Add 1-3 line items
                items_list = [
                    'Electronic Components', 'Raw Materials', 'Finished Goods',
                    'Packaging Materials', 'Machinery Parts', 'Textile Fabrics',
                ]
                for item_name in random.sample(items_list, random.randint(1, 3)):
                    qty = random.randint(10, 500)
                    unit_val = round(random.uniform(5, 200), 2)
                    TradeDocumentItem.objects.create(
                        trade_document=td,
                        item_description=item_name,
                        quantity=qty,
                        unit_value=unit_val,
                        total_value=round(qty * unit_val, 2),
                    )

            self.stdout.write(f'  Created {len(docs_created)} trade documents with line items.')

            # -----------------------------------------------------------------
            # 4. Licenses
            # -----------------------------------------------------------------
            license_data = [
                ('General Import License', 'import', 'Customs Authority'),
                ('Export Permit - Electronics', 'export', 'Trade Ministry'),
                ('Transit Permit - Chemicals', 'transit', 'Transport Authority'),
                ('Bonded Warehouse License', 'bonded_warehouse', 'Customs Authority'),
                ('Customs Broker Authorization', 'customs_broker', 'Customs Board'),
                ('Special Import Permit - Pharma', 'special_permit', 'Health Ministry'),
            ]
            license_statuses = ['draft', 'active', 'active', 'expiring_soon', 'expired', 'suspended']
            licenses_created = []

            for i, (title, ltype, authority) in enumerate(license_data):
                lic = License(
                    tenant=tenant,
                    title=title,
                    license_type=ltype,
                    issuing_authority=authority,
                    status=license_statuses[i % len(license_statuses)],
                    issue_date=today - timedelta(days=random.randint(60, 365)),
                    expiry_date=today + timedelta(days=random.randint(-30, 365)),
                    license_reference=f'GOV-{random.randint(100000, 999999)}',
                    country=random.choice(countries[:4]),
                    description=f'{title} for {tenant.name}.',
                    renewal_notes='Submit renewal 30 days before expiry.' if i % 2 == 0 else '',
                    created_by=random.choice(users),
                )
                lic.save()
                licenses_created.append(lic)

            self.stdout.write(f'  Created {len(licenses_created)} licenses.')

            # -----------------------------------------------------------------
            # 5. Sustainability Reports
            # -----------------------------------------------------------------
            report_types = ['carbon_footprint', 'ethical_sourcing', 'waste_management', 'energy_consumption', 'water_usage']
            report_statuses = ['draft', 'submitted', 'reviewed', 'approved', 'published']
            reports_created = []

            for i, rtype in enumerate(report_types):
                period_start = today - timedelta(days=90 * (i + 1))
                period_end = period_start + timedelta(days=90)
                sr = SustainabilityReport(
                    tenant=tenant,
                    title=f'{rtype.replace("_", " ").title()} Report Q{i + 1}',
                    report_type=rtype,
                    status=report_statuses[i % len(report_statuses)],
                    period_start=period_start,
                    period_end=period_end,
                    total_carbon_footprint=round(random.uniform(50, 500), 2),
                    carbon_offset=round(random.uniform(10, 100), 2),
                    sustainability_score=round(random.uniform(40, 95), 2),
                    description=f'{rtype.replace("_", " ").title()} assessment for {tenant.name}.',
                    recommendations='Continue current reduction strategies. Explore renewable energy options.',
                    created_by=random.choice(users),
                )
                sr.save()
                reports_created.append(sr)

                # Add 3-5 metrics
                metric_templates = [
                    ('CO2 Emissions', 'tons', 100, 150),
                    ('Energy Consumption', 'MWh', 200, 500),
                    ('Water Usage', 'm3', 500, 2000),
                    ('Waste Generated', 'tons', 10, 50),
                    ('Recycling Rate', '%', 60, 95),
                    ('Renewable Energy %', '%', 20, 80),
                    ('Supplier ESG Score', 'score', 50, 100),
                ]
                for m_name, m_unit, m_min, m_max in random.sample(metric_templates, random.randint(3, 5)):
                    val = round(random.uniform(m_min, m_max), 2)
                    target = round(random.uniform(m_min, m_max), 2)
                    SustainabilityMetric.objects.create(
                        report=sr,
                        metric_name=m_name,
                        value=val,
                        unit=m_unit,
                        target=target,
                        variance=round(val - target, 2),
                    )

            self.stdout.write(f'  Created {len(reports_created)} sustainability reports with metrics.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Contract & Compliance data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Superuser "admin" has no tenant — '
            'data won\'t appear when logged in as admin. '
            'Use a tenant admin account (e.g., admin_<slug>) to see the data.'
        ))
