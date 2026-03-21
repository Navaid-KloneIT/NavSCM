"""
Management command to seed the database with fake SRM data.

Usage:
    python manage.py seed_srm
    python manage.py seed_srm --flush  (clears SRM data first)

Requires: Tenants, users, and procurement vendors must exist first.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.procurement.models import Item, Vendor
from apps.srm.models import (
    CatalogItem,
    ContractMilestone,
    DueDiligenceCheck,
    QualificationQuestion,
    QualificationResponse,
    RiskFactor,
    RiskMitigationAction,
    ScorecardCriteria,
    ScorecardPeriod,
    SupplierCatalog,
    SupplierContract,
    SupplierOnboarding,
    SupplierRiskAssessment,
    SupplierScorecard,
)


class Command(BaseCommand):
    help = 'Seed the database with fake SRM data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing SRM data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing SRM data...'))
            RiskMitigationAction.objects.all().delete()
            RiskFactor.objects.all().delete()
            SupplierRiskAssessment.objects.all().delete()
            CatalogItem.objects.all().delete()
            SupplierCatalog.objects.all().delete()
            ContractMilestone.objects.all().delete()
            SupplierContract.objects.all().delete()
            ScorecardCriteria.objects.all().delete()
            SupplierScorecard.objects.all().delete()
            ScorecardPeriod.objects.all().delete()
            DueDiligenceCheck.objects.all().delete()
            QualificationResponse.objects.all().delete()
            SupplierOnboarding.objects.all().delete()
            QualificationQuestion.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All SRM data flushed.'))

        tenant_admins = []

        for tenant in tenants:
            self.stdout.write(f'\nSeeding SRM data for: {tenant.name}')
            users = list(User.objects.filter(tenant=tenant, is_active=True))

            if not users:
                self.stdout.write(self.style.WARNING('  No users found, skipping.'))
                continue

            vendors = list(Vendor.objects.filter(tenant=tenant, is_active=True))
            if not vendors:
                self.stdout.write(self.style.WARNING(
                    '  No vendors found. Run "python manage.py seed_procurement" first.'
                ))
                continue

            # Check if SRM data already exists for this tenant
            if SupplierOnboarding.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    '  SRM data already exists. Use --flush to re-seed.'
                ))
                continue

            # Find tenant admin for login info
            admin_user = User.objects.filter(
                tenant=tenant, is_tenant_admin=True
            ).first()
            if admin_user:
                tenant_admins.append(admin_user.username)

            user = users[0]

            questions = self._create_qualification_questions(tenant)
            periods = self._create_scorecard_periods(tenant)
            self._create_onboardings(tenant, vendors, users, user, questions)
            self._create_scorecards(tenant, vendors, user, periods)
            self._create_contracts(tenant, vendors, user)
            self._create_catalogs(tenant, vendors, user)
            self._create_risk_assessments(tenant, vendors, user)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('SRM seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('To see SRM data, log in as a tenant admin:')
        for username in tenant_admins:
            self.stdout.write(f'  Username: {username} / Password: password123')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: The superuser "admin" has no tenant, so SRM data '
            'will NOT appear when logged in as admin.'
        ))

    # -------------------------------------------------------------------------
    # Qualification Questions
    # -------------------------------------------------------------------------
    def _create_qualification_questions(self, tenant):
        questions_data = [
            ('general', 'Company legal name and registration number?', True, 1),
            ('general', 'Year of establishment?', True, 2),
            ('general', 'Number of employees?', False, 3),
            ('financial', 'Annual revenue for the last 3 years?', True, 1),
            ('financial', 'Bank references available?', False, 2),
            ('quality', 'ISO 9001 certified?', True, 1),
            ('quality', 'Quality control process description?', False, 2),
            ('compliance', 'Compliance with local labor laws?', True, 1),
            ('compliance', 'Anti-corruption policy in place?', True, 2),
            ('safety', 'Workplace safety certifications?', False, 1),
        ]

        questions = []
        for category, text, required, order in questions_data:
            q, _ = QualificationQuestion.objects.get_or_create(
                tenant=tenant,
                question_text=text,
                defaults={
                    'category': category,
                    'is_required': required,
                    'is_active': True,
                    'order': order,
                },
            )
            questions.append(q)

        self.stdout.write(f'  Created {len(questions)} qualification questions')
        return questions

    # -------------------------------------------------------------------------
    # Scorecard Periods
    # -------------------------------------------------------------------------
    def _create_scorecard_periods(self, tenant):
        periods_data = [
            ('Q1 2026', date(2026, 1, 1), date(2026, 3, 31)),
            ('Q2 2026', date(2026, 4, 1), date(2026, 6, 30)),
            ('Q3 2026', date(2026, 7, 1), date(2026, 9, 30)),
            ('Q4 2026', date(2026, 10, 1), date(2026, 12, 31)),
        ]

        periods = []
        for name, start, end in periods_data:
            p, _ = ScorecardPeriod.objects.get_or_create(
                tenant=tenant,
                name=name,
                defaults={
                    'start_date': start,
                    'end_date': end,
                    'is_active': True,
                },
            )
            periods.append(p)

        self.stdout.write(f'  Created {len(periods)} scorecard periods')
        return periods

    # -------------------------------------------------------------------------
    # Supplier Onboardings
    # -------------------------------------------------------------------------
    def _create_onboardings(self, tenant, vendors, users, user, questions):
        onboarding_data = [
            ('ONB-00001', 'draft', None),
            ('ONB-00002', 'under_review', None),
            ('ONB-00003', 'approved', timezone.now() - timedelta(days=5)),
        ]

        sample_responses = [
            'Acme Corp, Reg# 12345-XYZ',
            '2015',
            '250 full-time employees',
            '$5M (2023), $6.2M (2024), $7.1M (2025)',
            'Yes, Standard Chartered and HSBC',
            'Yes, ISO 9001:2015 certified since 2018',
            'We follow a 6-stage quality gate process with incoming, in-process, and final inspection.',
            'Fully compliant with all local labor regulations.',
            'Yes, anti-corruption policy adopted company-wide in 2020.',
            'OSHA 30-Hour certified, workplace safety audit passed 2025.',
        ]

        due_diligence_types = [
            ('financial_verification', 'Verify financial statements and credit rating'),
            ('legal_compliance', 'Check legal compliance and active litigation'),
            ('quality_certification', 'Verify ISO and quality certifications'),
            ('insurance_verification', 'Confirm insurance coverage and validity'),
            ('reference_check', 'Contact business references'),
            ('site_inspection', 'Conduct on-site facility inspection'),
        ]

        onboardings = []
        selected_vendors = vendors[:3] if len(vendors) >= 3 else vendors

        for idx, (number, status, reviewed_at) in enumerate(onboarding_data):
            if idx >= len(selected_vendors):
                break

            existing = SupplierOnboarding.objects.filter(
                tenant=tenant, onboarding_number=number
            ).first()
            if existing:
                onboardings.append(existing)
                continue

            vendor = selected_vendors[idx]
            reviewed_by = random.choice(users) if status in ('approved', 'rejected') else None

            onb = SupplierOnboarding.objects.create(
                tenant=tenant,
                vendor=vendor,
                onboarding_number=number,
                status=status,
                submitted_by=user,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                notes=f'Onboarding for {vendor.name}',
            )

            # Add qualification responses
            for q_idx, question in enumerate(questions):
                QualificationResponse.objects.get_or_create(
                    onboarding=onb,
                    question=question,
                    defaults={
                        'response_text': sample_responses[q_idx] if q_idx < len(sample_responses) else 'N/A',
                    },
                )

            # Add due diligence checks (3-4 per onboarding)
            num_checks = random.randint(3, 4)
            selected_checks = random.sample(due_diligence_types, k=num_checks)
            for check_type, description in selected_checks:
                dd_status = 'pending'
                checked_by = None
                checked_at = None
                if status == 'approved':
                    dd_status = 'passed'
                    checked_by = random.choice(users)
                    checked_at = timezone.now() - timedelta(days=random.randint(1, 10))
                elif status == 'under_review':
                    dd_status = random.choice(['pending', 'passed', 'passed'])
                    if dd_status == 'passed':
                        checked_by = random.choice(users)
                        checked_at = timezone.now() - timedelta(days=random.randint(1, 5))

                DueDiligenceCheck.objects.create(
                    onboarding=onb,
                    check_type=check_type,
                    description=description,
                    status=dd_status,
                    checked_by=checked_by,
                    checked_at=checked_at,
                    notes=f'{check_type.replace("_", " ").title()} check for {vendor.name}',
                )

            onboardings.append(onb)

        self.stdout.write(f'  Created {len(onboardings)} supplier onboardings with responses and due diligence checks')
        return onboardings

    # -------------------------------------------------------------------------
    # Supplier Scorecards
    # -------------------------------------------------------------------------
    def _create_scorecards(self, tenant, vendors, user, periods):
        scorecard_data = [
            # (number, rating, delivery, quality, price, responsiveness, status)
            ('SC-00001', 'excellent', Decimal('92.00'), Decimal('88.50'), Decimal('85.00'), Decimal('95.00'), 'approved'),
            ('SC-00002', 'good', Decimal('78.00'), Decimal('75.00'), Decimal('72.50'), Decimal('80.00'), 'submitted'),
            ('SC-00003', 'satisfactory', Decimal('62.00'), Decimal('58.00'), Decimal('55.00'), Decimal('65.00'), 'draft'),
        ]

        criteria_data = [
            ('delivery', 'On-time delivery rate', Decimal('25.00')),
            ('quality', 'Product quality compliance', Decimal('25.00')),
            ('price', 'Price competitiveness', Decimal('25.00')),
            ('responsiveness', 'Communication responsiveness', Decimal('25.00')),
        ]

        selected_vendors = vendors[:3] if len(vendors) >= 3 else vendors
        q1_period = periods[0]  # Q1 2026

        scorecards = []
        for idx, (number, rating, d_score, q_score, p_score, r_score, status) in enumerate(scorecard_data):
            if idx >= len(selected_vendors):
                break

            existing = SupplierScorecard.objects.filter(
                tenant=tenant, scorecard_number=number
            ).first()
            if existing:
                scorecards.append(existing)
                continue

            vendor = selected_vendors[idx]
            sc = SupplierScorecard(
                tenant=tenant,
                vendor=vendor,
                period=q1_period,
                scorecard_number=number,
                rating=rating,
                status=status,
                delivery_score=d_score,
                quality_score=q_score,
                price_score=p_score,
                responsiveness_score=r_score,
                notes=f'Performance evaluation for {vendor.name} - {q1_period.name}',
                evaluated_by=user,
                approved_by=user if status == 'approved' else None,
            )
            sc.save()  # save() calculates overall_score

            # Add 4 criteria (one per category)
            scores = [d_score, q_score, p_score, r_score]
            for c_idx, (category, name, weight) in enumerate(criteria_data):
                ScorecardCriteria.objects.create(
                    scorecard=sc,
                    category=category,
                    criteria_name=name,
                    weight=weight,
                    score=scores[c_idx],
                    notes=f'{name} score for {vendor.name}',
                )

            scorecards.append(sc)

        self.stdout.write(f'  Created {len(scorecards)} supplier scorecards with criteria')
        return scorecards

    # -------------------------------------------------------------------------
    # Supplier Contracts
    # -------------------------------------------------------------------------
    def _create_contracts(self, tenant, vendors, user):
        today = timezone.now().date()
        contract_data = [
            (
                'CON-00001', 'Master Supply Agreement', 'master_agreement', 'draft',
                today - timedelta(days=10), today + timedelta(days=355),
                Decimal('500000.00'), 'net_30',
            ),
            (
                'CON-00002', 'Annual Purchase Agreement', 'purchase_agreement', 'active',
                today - timedelta(days=90), today + timedelta(days=275),
                Decimal('250000.00'), 'net_45',
            ),
            (
                'CON-00003', 'Confidentiality Agreement', 'nda', 'active',
                today - timedelta(days=180), today + timedelta(days=25),
                Decimal('0.00'), 'net_30',
            ),
        ]

        milestone_data = {
            'CON-00001': [
                ('Contract negotiation complete', today + timedelta(days=15), 'pending'),
                ('Initial order placement', today + timedelta(days=45), 'pending'),
                ('First delivery milestone', today + timedelta(days=90), 'pending'),
            ],
            'CON-00002': [
                ('Quarterly review - Q1', today - timedelta(days=30), 'completed'),
                ('Quarterly review - Q2', today + timedelta(days=60), 'pending'),
                ('Annual renewal decision', today + timedelta(days=240), 'pending'),
            ],
            'CON-00003': [
                ('NDA compliance review', today + timedelta(days=10), 'pending'),
                ('Renewal discussion', today + timedelta(days=20), 'pending'),
            ],
        }

        selected_vendors = vendors[:3] if len(vendors) >= 3 else vendors

        contracts = []
        for idx, (number, title, ctype, status, start, end, value, terms) in enumerate(contract_data):
            if idx >= len(selected_vendors):
                break

            existing = SupplierContract.objects.filter(
                tenant=tenant, contract_number=number
            ).first()
            if existing:
                contracts.append(existing)
                continue

            vendor = selected_vendors[idx]
            contract = SupplierContract.objects.create(
                tenant=tenant,
                vendor=vendor,
                contract_number=number,
                title=title,
                description=f'{title} with {vendor.name}',
                contract_type=ctype,
                status=status,
                start_date=start,
                end_date=end,
                value=value,
                currency='USD',
                payment_terms=terms,
                auto_renew=idx == 1,
                renewal_notice_days=30,
                terms_conditions='Standard terms and conditions apply.',
                notes=f'Contract for {vendor.name}',
                created_by=user,
                approved_by=user if status == 'active' else None,
            )

            # Add milestones
            for m_title, m_due, m_status in milestone_data.get(number, []):
                completed_at = timezone.now() - timedelta(days=5) if m_status == 'completed' else None
                ContractMilestone.objects.create(
                    contract=contract,
                    title=m_title,
                    description=f'{m_title} for {contract.title}',
                    due_date=m_due,
                    status=m_status,
                    completed_at=completed_at,
                )

            contracts.append(contract)

        self.stdout.write(f'  Created {len(contracts)} supplier contracts with milestones')
        return contracts

    # -------------------------------------------------------------------------
    # Supplier Catalogs
    # -------------------------------------------------------------------------
    def _create_catalogs(self, tenant, vendors, user):
        today = timezone.now().date()
        catalog_data = [
            ('CAT-00001', 'Main Product Catalog', 'active', today - timedelta(days=30), today + timedelta(days=335)),
            ('CAT-00002', 'Seasonal Offerings', 'draft', None, None),
        ]

        selected_vendors = vendors[:2] if len(vendors) >= 2 else vendors
        items = list(Item.objects.filter(tenant=tenant, is_active=True)[:10])

        catalogs = []
        for idx, (number, name, status, eff_date, exp_date) in enumerate(catalog_data):
            if idx >= len(selected_vendors):
                break

            existing = SupplierCatalog.objects.filter(
                tenant=tenant, catalog_number=number
            ).first()
            if existing:
                catalogs.append(existing)
                continue

            vendor = selected_vendors[idx]
            catalog = SupplierCatalog.objects.create(
                tenant=tenant,
                vendor=vendor,
                catalog_number=number,
                name=name,
                description=f'{name} from {vendor.name}',
                status=status,
                effective_date=eff_date,
                expiry_date=exp_date,
                notes=f'Catalog for {vendor.name}',
                created_by=user,
            )

            # Add catalog items from procurement items
            if items:
                num_items = min(5, len(items))
                selected_items = items[idx * num_items:(idx + 1) * num_items]
                if not selected_items:
                    selected_items = items[:num_items]

                for item_idx, item in enumerate(selected_items):
                    variation = Decimal(str(random.uniform(0.85, 1.15)))
                    unit_price = (item.unit_price * variation).quantize(Decimal('0.01'))
                    CatalogItem.objects.create(
                        catalog=catalog,
                        item=item,
                        supplier_part_number=f'{vendor.code}-{item.code}',
                        description=item.name,
                        unit_of_measure=item.unit_of_measure,
                        unit_price=unit_price,
                        min_order_quantity=Decimal(str(random.choice([1, 5, 10, 25]))),
                        lead_time_days=random.randint(3, 21),
                        is_active=True,
                    )

            catalogs.append(catalog)

        self.stdout.write(f'  Created {len(catalogs)} supplier catalogs with items')
        return catalogs

    # -------------------------------------------------------------------------
    # Risk Assessments
    # -------------------------------------------------------------------------
    def _create_risk_assessments(self, tenant, vendors, user):
        today = timezone.now().date()
        assessment_data = [
            (
                'RA-00001', 'completed', 'low',
                Decimal('20.00'), Decimal('15.00'), Decimal('10.00'), Decimal('25.00'),
            ),
            (
                'RA-00002', 'in_progress', 'high',
                Decimal('70.00'), Decimal('60.00'), Decimal('75.00'), Decimal('65.00'),
            ),
        ]

        risk_factors_data = {
            'RA-00001': [
                ('financial', 'Credit risk', 'Low credit risk based on financial review', 1, 2, 'mitigated'),
                ('compliance', 'Regulatory compliance', 'All local regulations met', 1, 1, 'accepted'),
                ('operational', 'Supply chain disruption', 'Single source risk is low', 2, 2, 'monitoring'),
            ],
            'RA-00002': [
                ('financial', 'Liquidity concerns', 'Recent decline in cash flow reported', 4, 4, 'identified'),
                ('geopolitical', 'Trade restrictions', 'Potential new tariffs in sourcing region', 3, 5, 'identified'),
                ('compliance', 'Environmental violations', 'Past environmental fine on record', 3, 3, 'monitoring'),
                ('operational', 'Production capacity constraints', 'Operating near max capacity', 4, 3, 'identified'),
            ],
        }

        mitigation_actions_data = {
            'RA-00002': [
                ('financial', 0, 'Request updated financial statements and bank guarantees', today + timedelta(days=14)),
                ('geopolitical', 1, 'Identify alternative suppliers in different regions', today + timedelta(days=30)),
                ('compliance', 2, 'Request environmental audit report and corrective actions', today + timedelta(days=21)),
                ('operational', 3, 'Discuss capacity expansion plans with supplier', today + timedelta(days=10)),
            ],
        }

        selected_vendors = vendors[:2] if len(vendors) >= 2 else vendors

        assessments = []
        for idx, (number, status, risk_level, fin, geo, comp, ops) in enumerate(assessment_data):
            if idx >= len(selected_vendors):
                break

            existing = SupplierRiskAssessment.objects.filter(
                tenant=tenant, assessment_number=number
            ).first()
            if existing:
                assessments.append(existing)
                continue

            vendor = selected_vendors[idx]
            reviewed_by = user if status == 'completed' else None
            reviewed_at = timezone.now() - timedelta(days=3) if status == 'completed' else None

            ra = SupplierRiskAssessment(
                tenant=tenant,
                vendor=vendor,
                assessment_number=number,
                assessment_date=today - timedelta(days=random.randint(5, 30)),
                status=status,
                overall_risk_level=risk_level,
                financial_risk_score=fin,
                geopolitical_risk_score=geo,
                compliance_risk_score=comp,
                operational_risk_score=ops,
                notes=f'Risk assessment for {vendor.name}',
                assessed_by=user,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
            )
            ra.save()  # save() calculates overall_risk_score

            # Add risk factors
            factors = risk_factors_data.get(number, [])
            risk_factor_objs = []
            for category, name, desc, likelihood, impact, f_status in factors:
                rf = RiskFactor(
                    assessment=ra,
                    category=category,
                    factor_name=name,
                    description=desc,
                    likelihood=likelihood,
                    impact=impact,
                    mitigation_plan=f'Mitigation plan for {name}' if f_status != 'accepted' else '',
                    status=f_status,
                )
                rf.save()  # save() calculates risk_score
                risk_factor_objs.append(rf)

            # Add mitigation actions for high-risk assessment
            actions = mitigation_actions_data.get(number, [])
            for _cat, factor_idx, action_desc, due_date in actions:
                if factor_idx < len(risk_factor_objs):
                    RiskMitigationAction.objects.create(
                        risk_factor=risk_factor_objs[factor_idx],
                        action_description=action_desc,
                        assigned_to=user,
                        due_date=due_date,
                        status='pending',
                    )

            assessments.append(ra)

        self.stdout.write(f'  Created {len(assessments)} risk assessments with factors and mitigations')
        return assessments
