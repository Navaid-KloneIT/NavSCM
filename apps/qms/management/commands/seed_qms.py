import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Tenant
from apps.procurement.models import Item
from apps.qms.models import (
    AuditFinding,
    CAPA,
    CAPAAction,
    CertificateOfAnalysis,
    CoATestResult,
    InspectionCriteria,
    InspectionResult,
    InspectionTemplate,
    NonConformanceReport,
    QualityAudit,
    QualityInspection,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample QMS (Quality Management System) data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing QMS data before seeding',
        )

    def handle(self, *args, **options):
        tenants = list(Tenant.objects.filter(is_active=True))

        if not tenants:
            self.stdout.write(self.style.ERROR(
                'No tenants found. Run "python manage.py seed_data" first.'
            ))
            return

        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing QMS data...'))
            CoATestResult.objects.all().delete()
            CertificateOfAnalysis.objects.all().delete()
            AuditFinding.objects.all().delete()
            QualityAudit.objects.all().delete()
            CAPAAction.objects.all().delete()
            CAPA.objects.all().delete()
            NonConformanceReport.objects.all().delete()
            InspectionResult.objects.all().delete()
            QualityInspection.objects.all().delete()
            InspectionCriteria.objects.all().delete()
            InspectionTemplate.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All QMS data flushed.'))

        for tenant in tenants:
            self.stdout.write(f'\nSeeding QMS data for: {tenant.name}')
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

            if InspectionTemplate.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    '  QMS data already exists. Use --flush to re-seed.'
                ))
                continue

            templates = self._create_inspection_templates(tenant, users)
            inspections = self._create_quality_inspections(tenant, users, items, templates)
            ncrs = self._create_ncrs(tenant, users, items, inspections)
            self._create_capas(tenant, users, ncrs)
            self._create_audits(tenant, users)
            self._create_coas(tenant, users, items)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('QMS seeding complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Log in as a tenant admin (e.g., admin_<slug>) to see module data.'
        ))
        self.stdout.write(self.style.WARNING(
            'Superuser "admin" has no tenant — data will not appear.'
        ))

    # -------------------------------------------------------------------------
    # INSPECTION TEMPLATES
    # -------------------------------------------------------------------------
    def _create_inspection_templates(self, tenant, users):
        templates_data = [
            {
                'name': 'Incoming Material Inspection',
                'inspection_type': 'incoming',
                'description': 'Standard inspection template for incoming raw materials and components.',
                'criteria': [
                    {'seq': 10, 'name': 'Visual Appearance', 'measurement_type': 'visual',
                     'acceptance_criteria': 'No visible defects, scratches, or discoloration',
                     'description': 'Check for surface defects and color consistency'},
                    {'seq': 20, 'name': 'Dimensional Accuracy', 'measurement_type': 'dimensional',
                     'acceptance_criteria': 'Within +/- 0.5mm of specification',
                     'description': 'Measure critical dimensions against drawing specs'},
                    {'seq': 30, 'name': 'Weight Check', 'measurement_type': 'mechanical',
                     'acceptance_criteria': 'Within +/- 2% of nominal weight',
                     'description': 'Verify weight against specification sheet'},
                    {'seq': 40, 'name': 'Packaging Integrity', 'measurement_type': 'visual',
                     'acceptance_criteria': 'Packaging undamaged, labels intact and legible',
                     'description': 'Inspect packaging for damage during transit'},
                ],
            },
            {
                'name': 'In-Process Quality Check',
                'inspection_type': 'in_process',
                'description': 'Quality check template for in-process manufacturing stages.',
                'criteria': [
                    {'seq': 10, 'name': 'Assembly Alignment', 'measurement_type': 'dimensional',
                     'acceptance_criteria': 'All components aligned within 0.1mm tolerance',
                     'description': 'Verify assembly alignment at key junction points'},
                    {'seq': 20, 'name': 'Functional Test', 'measurement_type': 'functional',
                     'acceptance_criteria': 'All functions operate per test protocol',
                     'description': 'Run standard functional test sequence'},
                    {'seq': 30, 'name': 'Surface Finish', 'measurement_type': 'visual',
                     'acceptance_criteria': 'Ra <= 1.6 um, no burrs or tool marks',
                     'description': 'Inspect surface finish quality'},
                ],
            },
            {
                'name': 'Final Product Inspection',
                'inspection_type': 'final',
                'description': 'Comprehensive inspection template for finished products before shipment.',
                'criteria': [
                    {'seq': 10, 'name': 'Overall Appearance', 'measurement_type': 'visual',
                     'acceptance_criteria': 'Product meets cosmetic standards, no blemishes',
                     'description': 'Full visual inspection of finished product'},
                    {'seq': 20, 'name': 'Electrical Safety', 'measurement_type': 'electrical',
                     'acceptance_criteria': 'Insulation resistance > 10 MOhm, leakage < 0.5mA',
                     'description': 'Perform electrical safety tests per IEC standards'},
                    {'seq': 30, 'name': 'Performance Test', 'measurement_type': 'functional',
                     'acceptance_criteria': 'Output within specified range under load conditions',
                     'description': 'Run full performance test under rated conditions'},
                    {'seq': 40, 'name': 'Label Accuracy', 'measurement_type': 'visual',
                     'acceptance_criteria': 'All labels correct, legible, and properly positioned',
                     'description': 'Verify product labels, barcodes, and regulatory markings'},
                    {'seq': 50, 'name': 'Package Seal', 'measurement_type': 'mechanical',
                     'acceptance_criteria': 'Seal integrity verified, vacuum test passed',
                     'description': 'Test package seal strength and integrity'},
                ],
            },
        ]

        results = []
        for data in templates_data:
            template, created = InspectionTemplate.objects.get_or_create(
                tenant=tenant,
                name=data['name'],
                defaults={
                    'inspection_type': data['inspection_type'],
                    'description': data['description'],
                    'is_active': True,
                    'created_by': random.choice(users),
                },
            )
            if created:
                for crit_data in data['criteria']:
                    InspectionCriteria.objects.create(
                        template=template,
                        sequence=crit_data['seq'],
                        name=crit_data['name'],
                        measurement_type=crit_data['measurement_type'],
                        acceptance_criteria=crit_data['acceptance_criteria'],
                        description=crit_data['description'],
                        is_required=True,
                    )
            results.append(template)
        self.stdout.write(f'  Created {len(results)} inspection templates with criteria')
        return results

    # -------------------------------------------------------------------------
    # QUALITY INSPECTIONS
    # -------------------------------------------------------------------------
    def _create_quality_inspections(self, tenant, users, items, templates):
        now = timezone.now()
        today = now.date()

        inspections_data = [
            {
                'template_idx': 0,
                'inspection_type': 'incoming',
                'status': 'draft',
                'lot_number': 'LOT-2026-001',
                'sample_size': 10,
                'accepted_quantity': Decimal('0.00'),
                'rejected_quantity': Decimal('0.00'),
                'inspection_date': None,
                'notes': 'Draft inspection for incoming steel components. Awaiting inspector assignment.',
                'results': [
                    {'result': 'pass', 'measured_value': 'No defects', 'notes': 'Clean surface'},
                    {'result': 'pass', 'measured_value': '25.3mm', 'notes': 'Within tolerance'},
                    {'result': 'warning', 'measured_value': '4.92kg', 'notes': 'Slightly below nominal'},
                ],
            },
            {
                'template_idx': 1,
                'inspection_type': 'in_process',
                'status': 'in_progress',
                'lot_number': 'LOT-2026-002',
                'sample_size': 5,
                'accepted_quantity': Decimal('3.00'),
                'rejected_quantity': Decimal('0.00'),
                'inspection_date': today,
                'notes': 'In-process quality check on assembly line B. Partially complete.',
                'results': [
                    {'result': 'pass', 'measured_value': '0.05mm deviation', 'notes': 'Alignment OK'},
                    {'result': 'pass', 'measured_value': 'All functions nominal', 'notes': 'Test passed'},
                    {'result': 'warning', 'measured_value': 'Ra 1.4 um', 'notes': 'Approaching upper limit'},
                    {'result': 'pass', 'measured_value': 'No burrs detected', 'notes': ''},
                ],
            },
            {
                'template_idx': 2,
                'inspection_type': 'final',
                'status': 'completed',
                'lot_number': 'LOT-2026-003',
                'sample_size': 20,
                'accepted_quantity': Decimal('19.00'),
                'rejected_quantity': Decimal('1.00'),
                'inspection_date': today - timedelta(days=3),
                'notes': 'Final inspection completed. 95% pass rate. One unit with cosmetic defect.',
                'results': [
                    {'result': 'pass', 'measured_value': 'Excellent finish', 'notes': ''},
                    {'result': 'pass', 'measured_value': '> 50 MOhm', 'notes': 'Well above threshold'},
                    {'result': 'pass', 'measured_value': '98.2% efficiency', 'notes': 'Within spec'},
                    {'result': 'fail', 'measured_value': 'Label offset 3mm', 'notes': 'Label misaligned on 1 unit'},
                    {'result': 'pass', 'measured_value': 'Seal intact', 'notes': 'Vacuum test passed'},
                ],
            },
            {
                'template_idx': 0,
                'inspection_type': 'incoming',
                'status': 'failed',
                'lot_number': 'LOT-2026-004',
                'sample_size': 15,
                'accepted_quantity': Decimal('5.00'),
                'rejected_quantity': Decimal('10.00'),
                'inspection_date': today - timedelta(days=5),
                'notes': 'Incoming batch failed inspection. Significant dimensional issues. Supplier notified.',
                'results': [
                    {'result': 'fail', 'measured_value': 'Visible scratches', 'notes': 'Surface damage on 8 units'},
                    {'result': 'fail', 'measured_value': '26.8mm', 'notes': 'Exceeds tolerance by 1.0mm'},
                    {'result': 'fail', 'measured_value': '4.1kg', 'notes': 'Below minimum weight'},
                    {'result': 'warning', 'measured_value': 'Minor dents', 'notes': 'Packaging damaged during transit'},
                ],
            },
            {
                'template_idx': 1,
                'inspection_type': 'in_process',
                'status': 'on_hold',
                'lot_number': 'LOT-2026-005',
                'sample_size': 8,
                'accepted_quantity': Decimal('4.00'),
                'rejected_quantity': Decimal('2.00'),
                'inspection_date': today - timedelta(days=1),
                'notes': 'Inspection on hold pending calibration of measurement equipment.',
                'results': [
                    {'result': 'pass', 'measured_value': '0.08mm', 'notes': 'Within tolerance'},
                    {'result': 'fail', 'measured_value': 'Intermittent fault', 'notes': 'Function test failed on 2 units'},
                    {'result': 'pass', 'measured_value': 'Ra 0.8 um', 'notes': 'Good surface finish'},
                ],
            },
        ]

        results = []
        for i, data in enumerate(inspections_data):
            item = items[i % len(items)]
            user = random.choice(users)
            template = templates[data['template_idx']]
            criteria_list = list(template.criteria.all())

            inspection = QualityInspection(
                tenant=tenant,
                template=template,
                item=item,
                inspection_type=data['inspection_type'],
                status=data['status'],
                inspector=random.choice(users),
                inspection_date=data['inspection_date'],
                lot_number=data['lot_number'],
                sample_size=data['sample_size'],
                accepted_quantity=data['accepted_quantity'],
                rejected_quantity=data['rejected_quantity'],
                notes=data['notes'],
                created_by=user,
            )
            inspection.save()

            for j, res_data in enumerate(data['results']):
                criteria = criteria_list[j % len(criteria_list)] if criteria_list else None
                InspectionResult.objects.create(
                    inspection=inspection,
                    criteria=criteria,
                    result=res_data['result'],
                    measured_value=res_data['measured_value'],
                    notes=res_data['notes'],
                )
            results.append(inspection)
        self.stdout.write(f'  Created {len(results)} quality inspections with results')
        return results

    # -------------------------------------------------------------------------
    # NON-CONFORMANCE REPORTS
    # -------------------------------------------------------------------------
    def _create_ncrs(self, tenant, users, items, inspections):
        now = timezone.now()
        today = now.date()

        failed_inspections = [i for i in inspections if i.status == 'failed']
        completed_inspections = [i for i in inspections if i.status == 'completed']

        ncrs_data = [
            {
                'title': 'Dimensional Non-Conformance on Incoming Steel',
                'source': 'incoming_inspection',
                'severity': 'major',
                'status': 'draft',
                'description': 'Incoming steel components exceed dimensional tolerances. '
                               'Measured 26.8mm vs 25.5mm spec on critical dimension.',
                'root_cause': '',
                'disposition': '',
                'disposition_notes': '',
                'quantity_affected': Decimal('10.00'),
                'reported_date': today,
                'closed_date': None,
                'notes': 'Awaiting quality manager review before opening.',
                'inspection': failed_inspections[0] if failed_inspections else None,
            },
            {
                'title': 'Surface Finish Defect on Assembly Line B',
                'source': 'in_process',
                'severity': 'minor',
                'status': 'open',
                'description': 'Surface finish on 3 units shows tool marks exceeding Ra 1.6 um limit. '
                               'Likely caused by worn tooling on station 5.',
                'root_cause': '',
                'disposition': '',
                'disposition_notes': '',
                'quantity_affected': Decimal('3.00'),
                'reported_date': today - timedelta(days=2),
                'closed_date': None,
                'notes': 'Assigned to manufacturing team for investigation.',
                'inspection': None,
            },
            {
                'title': 'Customer Complaint - Intermittent Power Failure',
                'source': 'customer_complaint',
                'severity': 'critical',
                'status': 'under_investigation',
                'description': 'Customer reported intermittent power failure on 5 units from batch LOT-2026-003. '
                               'Potential solder joint issue on main PCB.',
                'root_cause': 'Preliminary analysis points to cold solder joints on connector J4.',
                'disposition': '',
                'disposition_notes': '',
                'quantity_affected': Decimal('5.00'),
                'reported_date': today - timedelta(days=7),
                'closed_date': None,
                'notes': 'Failure analysis in progress. Cross-functional team assigned.',
                'inspection': completed_inspections[0] if completed_inspections else None,
            },
            {
                'title': 'Supplier Material Certificate Discrepancy',
                'source': 'supplier_issue',
                'severity': 'minor',
                'status': 'resolved',
                'description': 'Material certificate from supplier XYZ shows alloy composition outside '
                               'specified range. Actual Cr content 17.8% vs 18-20% specification.',
                'root_cause': 'Supplier used incorrect alloy batch. Certificate confirmed correct but material was wrong.',
                'disposition': 'return_to_supplier',
                'disposition_notes': 'Full batch returned to supplier. Replacement shipment expected in 5 business days.',
                'quantity_affected': Decimal('500.00'),
                'reported_date': today - timedelta(days=14),
                'closed_date': today - timedelta(days=3),
                'notes': 'Supplier has acknowledged the issue and issued credit.',
                'inspection': None,
            },
        ]

        results = []
        for i, data in enumerate(ncrs_data):
            item = items[i % len(items)]
            user = random.choice(users)

            ncr = NonConformanceReport(
                tenant=tenant,
                title=data['title'],
                item=item,
                inspection=data['inspection'],
                source=data['source'],
                severity=data['severity'],
                status=data['status'],
                description=data['description'],
                root_cause=data['root_cause'],
                disposition=data['disposition'],
                disposition_notes=data['disposition_notes'],
                quantity_affected=data['quantity_affected'],
                reported_by=random.choice(users),
                assigned_to=random.choice(users),
                reported_date=data['reported_date'],
                closed_date=data['closed_date'],
                notes=data['notes'],
                created_by=user,
            )
            ncr.save()
            results.append(ncr)
        self.stdout.write(f'  Created {len(results)} non-conformance reports')
        return results

    # -------------------------------------------------------------------------
    # CAPAs
    # -------------------------------------------------------------------------
    def _create_capas(self, tenant, users, ncrs):
        now = timezone.now()
        today = now.date()

        capas_data = [
            {
                'title': 'Corrective Action - Incoming Inspection Process',
                'capa_type': 'corrective',
                'status': 'draft',
                'priority': 'high',
                'description': 'Implement corrective actions to prevent recurrence of dimensional '
                               'non-conformances on incoming materials.',
                'root_cause_analysis': '',
                'due_date': today + timedelta(days=30),
                'completed_date': None,
                'ncr_idx': 0,
                'notes': 'Draft CAPA pending root cause analysis completion.',
                'actions': [
                    {'seq': 10, 'description': 'Review and update incoming inspection procedure to include 100% dimensional check',
                     'status': 'pending', 'due_date': today + timedelta(days=14)},
                    {'seq': 20, 'description': 'Issue supplier corrective action request (SCAR)',
                     'status': 'pending', 'due_date': today + timedelta(days=7)},
                ],
            },
            {
                'title': 'Corrective Action - Solder Joint Quality',
                'capa_type': 'corrective',
                'status': 'in_progress',
                'priority': 'critical',
                'description': 'Address cold solder joint issue on connector J4 affecting product reliability. '
                               'Root cause: reflow oven profile drift.',
                'root_cause_analysis': 'Investigation revealed reflow oven Zone 3 temperature drifted 8C below '
                                       'setpoint due to thermocouple degradation. This resulted in insufficient '
                                       'solder reflow on high-thermal-mass connectors.',
                'due_date': today + timedelta(days=21),
                'completed_date': None,
                'ncr_idx': 2,
                'notes': 'Critical priority. Production hold until oven profile verified.',
                'actions': [
                    {'seq': 10, 'description': 'Replace thermocouple in reflow oven Zone 3',
                     'status': 'completed', 'due_date': today - timedelta(days=1),
                     'completed_date': today - timedelta(days=1)},
                    {'seq': 20, 'description': 'Re-validate reflow oven temperature profile',
                     'status': 'in_progress', 'due_date': today + timedelta(days=3)},
                    {'seq': 30, 'description': 'Implement weekly oven profile verification check',
                     'status': 'pending', 'due_date': today + timedelta(days=14)},
                    {'seq': 40, 'description': 'Rework affected units from LOT-2026-003',
                     'status': 'pending', 'due_date': today + timedelta(days=10)},
                ],
            },
            {
                'title': 'Preventive Action - Supplier Quality Program Enhancement',
                'capa_type': 'preventive',
                'status': 'completed',
                'priority': 'medium',
                'description': 'Enhance supplier quality program to prevent material certificate '
                               'discrepancies and improve incoming material quality.',
                'root_cause_analysis': 'Analysis of past 12 months shows 3 incidents of supplier material '
                                       'non-conformance. Current supplier audit frequency is insufficient.',
                'due_date': today - timedelta(days=5),
                'completed_date': today - timedelta(days=5),
                'ncr_idx': 3,
                'notes': 'All actions completed. Effectiveness review scheduled for next quarter.',
                'actions': [
                    {'seq': 10, 'description': 'Increase supplier audit frequency from annual to semi-annual',
                     'status': 'completed', 'due_date': today - timedelta(days=14),
                     'completed_date': today - timedelta(days=14)},
                    {'seq': 20, 'description': 'Require third-party material certification for critical alloys',
                     'status': 'completed', 'due_date': today - timedelta(days=10),
                     'completed_date': today - timedelta(days=10)},
                    {'seq': 30, 'description': 'Update supplier quality manual with new requirements',
                     'status': 'completed', 'due_date': today - timedelta(days=7),
                     'completed_date': today - timedelta(days=7)},
                ],
            },
        ]

        results = []
        for i, data in enumerate(capas_data):
            user = random.choice(users)
            ncr = ncrs[data['ncr_idx']] if data['ncr_idx'] < len(ncrs) else None

            capa = CAPA(
                tenant=tenant,
                title=data['title'],
                capa_type=data['capa_type'],
                ncr=ncr,
                status=data['status'],
                priority=data['priority'],
                description=data['description'],
                root_cause_analysis=data['root_cause_analysis'],
                due_date=data['due_date'],
                completed_date=data['completed_date'],
                assigned_to=random.choice(users),
                notes=data['notes'],
                created_by=user,
            )
            if data['status'] == 'completed':
                capa.verified_by = random.choice(users)
                capa.verification_notes = 'All actions verified as effective. No recurrence observed.'
            capa.save()

            for act_data in data['actions']:
                CAPAAction.objects.create(
                    capa=capa,
                    sequence=act_data['seq'],
                    description=act_data['description'],
                    assigned_to=random.choice(users),
                    due_date=act_data['due_date'],
                    completed_date=act_data.get('completed_date'),
                    status=act_data['status'],
                    notes='',
                )
            results.append(capa)
        self.stdout.write(f'  Created {len(results)} CAPAs with actions')
        return results

    # -------------------------------------------------------------------------
    # QUALITY AUDITS
    # -------------------------------------------------------------------------
    def _create_audits(self, tenant, users):
        now = timezone.now()
        today = now.date()

        audits_data = [
            {
                'title': 'Q1 2026 Internal Quality System Audit',
                'audit_type': 'internal',
                'status': 'draft',
                'scope': 'Review of document control, corrective action process, and '
                         'management review procedures per ISO 9001:2015 clauses 7.5, 10.2, 9.3.',
                'audit_date': today + timedelta(days=14),
                'completion_date': None,
                'findings_summary': '',
                'notes': 'Scheduled for next month. Audit plan distributed to department heads.',
                'findings': [
                    {'number': 1, 'title': 'Document Control Procedure Review',
                     'description': 'Planned review of document control procedures',
                     'finding_type': 'observation', 'severity': 'low', 'status': 'open',
                     'due_date': today + timedelta(days=28)},
                    {'number': 2, 'title': 'Training Records Completeness Check',
                     'description': 'Verify training records are current for all quality personnel',
                     'finding_type': 'observation', 'severity': 'low', 'status': 'open',
                     'due_date': today + timedelta(days=28)},
                ],
            },
            {
                'title': 'Supplier XYZ Quality Audit',
                'audit_type': 'supplier',
                'status': 'in_progress',
                'scope': 'Comprehensive supplier quality audit covering manufacturing process, '
                         'quality control, material traceability, and corrective action systems.',
                'audit_date': today - timedelta(days=3),
                'completion_date': None,
                'findings_summary': 'Preliminary findings indicate strong manufacturing controls but '
                                    'gaps in corrective action follow-up.',
                'notes': 'On-site audit in progress. Day 2 of 3.',
                'findings': [
                    {'number': 1, 'title': 'Corrective Action Timeliness',
                     'description': '3 of 8 reviewed CAPAs exceeded target completion date by >30 days',
                     'finding_type': 'minor_nc', 'severity': 'medium', 'status': 'open',
                     'due_date': today + timedelta(days=45)},
                    {'number': 2, 'title': 'Excellent SPC Implementation',
                     'description': 'Statistical process control charts well-maintained with proper reaction plans',
                     'finding_type': 'positive', 'severity': 'low', 'status': 'closed',
                     'due_date': None},
                    {'number': 3, 'title': 'Calibration Record Gap',
                     'description': 'Micrometer #M-042 missing calibration record for Q4 2025',
                     'finding_type': 'minor_nc', 'severity': 'medium', 'status': 'open',
                     'due_date': today + timedelta(days=30)},
                ],
            },
            {
                'title': 'External ISO 9001 Surveillance Audit',
                'audit_type': 'external',
                'status': 'completed',
                'scope': 'Annual surveillance audit by certification body covering clauses 4-10 '
                         'of ISO 9001:2015 with focus on risk-based thinking and process approach.',
                'audit_date': today - timedelta(days=30),
                'completion_date': today - timedelta(days=28),
                'findings_summary': 'Audit completed successfully. One minor NC and two opportunities '
                                    'for improvement identified. Certification maintained.',
                'notes': 'Next surveillance audit scheduled for Q1 2027.',
                'findings': [
                    {'number': 1, 'title': 'Risk Register Update Frequency',
                     'description': 'Risk register not updated per defined schedule. Last update was 8 months ago.',
                     'finding_type': 'minor_nc', 'severity': 'medium', 'status': 'in_progress',
                     'corrective_action': 'Assign risk register ownership and set quarterly review schedule',
                     'due_date': today + timedelta(days=60)},
                    {'number': 2, 'title': 'Customer Satisfaction Monitoring Enhancement',
                     'description': 'Consider expanding customer satisfaction metrics beyond survey scores',
                     'finding_type': 'opportunity_for_improvement', 'severity': 'low', 'status': 'open',
                     'due_date': today + timedelta(days=90)},
                    {'number': 3, 'title': 'Strong Competence Management',
                     'description': 'Training program and competence matrix well-implemented across all departments',
                     'finding_type': 'positive', 'severity': 'low', 'status': 'closed',
                     'due_date': None},
                    {'number': 4, 'title': 'Internal Audit Program Scheduling',
                     'description': 'Consider risk-based approach to internal audit scheduling for better resource allocation',
                     'finding_type': 'opportunity_for_improvement', 'severity': 'low', 'status': 'open',
                     'due_date': today + timedelta(days=90)},
                ],
            },
        ]

        results = []
        for data in audits_data:
            user = random.choice(users)

            audit = QualityAudit(
                tenant=tenant,
                title=data['title'],
                audit_type=data['audit_type'],
                status=data['status'],
                scope=data['scope'],
                lead_auditor=random.choice(users),
                audit_date=data['audit_date'],
                completion_date=data['completion_date'],
                findings_summary=data['findings_summary'],
                notes=data['notes'],
                created_by=user,
            )
            audit.save()

            for f_data in data['findings']:
                AuditFinding.objects.create(
                    audit=audit,
                    finding_number=f_data['number'],
                    title=f_data['title'],
                    description=f_data['description'],
                    finding_type=f_data['finding_type'],
                    severity=f_data['severity'],
                    assigned_to=random.choice(users),
                    due_date=f_data['due_date'],
                    status=f_data['status'],
                    corrective_action=f_data.get('corrective_action', ''),
                    notes='',
                )
            results.append(audit)
        self.stdout.write(f'  Created {len(results)} quality audits with findings')
        return results

    # -------------------------------------------------------------------------
    # CERTIFICATES OF ANALYSIS
    # -------------------------------------------------------------------------
    def _create_coas(self, tenant, users, items):
        now = timezone.now()
        today = now.date()

        coas_data = [
            {
                'title': 'CoA - Steel Alloy Batch SA-2026-A1',
                'batch_number': 'SA-2026-A1',
                'status': 'draft',
                'quantity': Decimal('1000.00'),
                'unit_of_measure': 'kg',
                'production_date': today - timedelta(days=10),
                'expiry_date': today + timedelta(days=355),
                'approved_by': None,
                'approved_date': None,
                'notes': 'Draft CoA for incoming steel alloy batch. Pending lab results.',
                'test_results': [
                    {'seq': 10, 'test_name': 'Tensile Strength', 'test_method': 'ASTM E8',
                     'specification': '515-690 MPa', 'result': '582 MPa', 'uom': 'MPa', 'status': 'pass'},
                    {'seq': 20, 'test_name': 'Yield Strength', 'test_method': 'ASTM E8',
                     'specification': '> 205 MPa', 'result': '318 MPa', 'uom': 'MPa', 'status': 'pass'},
                    {'seq': 30, 'test_name': 'Chromium Content', 'test_method': 'ASTM E1086',
                     'specification': '18.0 - 20.0%', 'result': '18.4%', 'uom': '%', 'status': 'pass'},
                    {'seq': 40, 'test_name': 'Carbon Content', 'test_method': 'ASTM E1086',
                     'specification': '< 0.08%', 'result': '0.05%', 'uom': '%', 'status': 'pass'},
                    {'seq': 50, 'test_name': 'Hardness', 'test_method': 'ASTM E18',
                     'specification': '< 92 HRB', 'result': '85 HRB', 'uom': 'HRB', 'status': 'pass'},
                ],
            },
            {
                'title': 'CoA - Electronic Module Batch EM-2026-Q1',
                'batch_number': 'EM-2026-Q1',
                'status': 'approved',
                'quantity': Decimal('500.00'),
                'unit_of_measure': 'piece',
                'production_date': today - timedelta(days=20),
                'expiry_date': None,
                'notes': 'Approved CoA for electronic modules. All tests passed.',
                'test_results': [
                    {'seq': 10, 'test_name': 'Input Voltage Range', 'test_method': 'IEC 61010',
                     'specification': '100-240V AC', 'result': '98-242V AC', 'uom': 'V', 'status': 'pass'},
                    {'seq': 20, 'test_name': 'Output Power', 'test_method': 'Internal TP-201',
                     'specification': '48W +/- 5%', 'result': '47.8W', 'uom': 'W', 'status': 'pass'},
                    {'seq': 30, 'test_name': 'Insulation Resistance', 'test_method': 'IEC 61010',
                     'specification': '> 10 MOhm', 'result': '45 MOhm', 'uom': 'MOhm', 'status': 'pass'},
                    {'seq': 40, 'test_name': 'Operating Temperature', 'test_method': 'Internal TP-205',
                     'specification': '-10 to 55 C', 'result': '-12 to 58 C', 'uom': 'C', 'status': 'fail',
                     'notes': 'Marginal fail on upper limit. Acceptable per engineering review.'},
                ],
            },
            {
                'title': 'CoA - Polymer Resin Batch PR-2026-03',
                'batch_number': 'PR-2026-03',
                'status': 'issued',
                'quantity': Decimal('250.00'),
                'unit_of_measure': 'kg',
                'production_date': today - timedelta(days=45),
                'expiry_date': today + timedelta(days=320),
                'notes': 'Issued CoA for polymer resin. Shipped with material to customer.',
                'test_results': [
                    {'seq': 10, 'test_name': 'Melt Flow Index', 'test_method': 'ASTM D1238',
                     'specification': '10-15 g/10min', 'result': '12.3 g/10min', 'uom': 'g/10min', 'status': 'pass'},
                    {'seq': 20, 'test_name': 'Density', 'test_method': 'ASTM D792',
                     'specification': '0.94-0.96 g/cm3', 'result': '0.952 g/cm3', 'uom': 'g/cm3', 'status': 'pass'},
                    {'seq': 30, 'test_name': 'Moisture Content', 'test_method': 'ASTM D6980',
                     'specification': '< 0.1%', 'result': '0.04%', 'uom': '%', 'status': 'pass'},
                ],
            },
        ]

        results = []
        for i, data in enumerate(coas_data):
            item = items[i % len(items)]
            user = random.choice(users)

            coa = CertificateOfAnalysis(
                tenant=tenant,
                title=data['title'],
                item=item,
                batch_number=data['batch_number'],
                production_date=data['production_date'],
                expiry_date=data.get('expiry_date'),
                status=data['status'],
                quantity=data['quantity'],
                unit_of_measure=data['unit_of_measure'],
                notes=data['notes'],
                created_by=user,
            )
            if data['status'] in ('approved', 'issued'):
                coa.approved_by = random.choice(users)
                coa.approved_date = today - timedelta(days=random.randint(1, 10))
            coa.save()

            for tr_data in data['test_results']:
                CoATestResult.objects.create(
                    coa=coa,
                    sequence=tr_data['seq'],
                    test_name=tr_data['test_name'],
                    test_method=tr_data['test_method'],
                    specification=tr_data['specification'],
                    result=tr_data['result'],
                    unit_of_measure=tr_data['uom'],
                    status=tr_data['status'],
                    notes=tr_data.get('notes', ''),
                )
            results.append(coa)
        self.stdout.write(f'  Created {len(results)} certificates of analysis with test results')
        return results
