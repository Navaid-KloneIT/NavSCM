import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cold_chain.models import (
    ColdStorageItem,
    ColdStorageUnit,
    ComplianceReport,
    ComplianceReportItem,
    ReeferMaintenance,
    ReeferUnit,
    TemperatureExcursion,
    TemperatureReading,
    TemperatureSensor,
    TemperatureZone,
)
from apps.core.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample Cold Chain Management data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete existing cold chain data before seeding.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
            self.stdout.write(self.style.ERROR('No active tenants found. Run seed_data first.'))
            return

        if options['flush']:
            self.stdout.write('Flushing existing cold chain data...')
            ReeferMaintenance.objects.all().delete()
            ReeferUnit.objects.all().delete()
            ComplianceReportItem.objects.all().delete()
            ComplianceReport.objects.all().delete()
            ColdStorageItem.objects.all().delete()
            ColdStorageUnit.objects.all().delete()
            TemperatureExcursion.objects.all().delete()
            TemperatureReading.objects.all().delete()
            TemperatureSensor.objects.all().delete()
            TemperatureZone.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Flushed.'))

        today = timezone.now().date()
        now = timezone.now()

        for tenant in tenants:
            self.stdout.write(f'\nSeeding cold chain data for tenant: {tenant.name}')

            users = list(User.objects.filter(tenant=tenant, is_active=True)[:5])

            if not users:
                self.stdout.write(self.style.WARNING(f'  No users for {tenant.name}. Skipping.'))
                continue

            if TemperatureZone.objects.filter(tenant=tenant).exists():
                self.stdout.write(self.style.WARNING(
                    f'  Data already exists for {tenant.name}. Use --flush to re-seed.'
                ))
                continue

            # -----------------------------------------------------------------
            # 1. Temperature Zones (5)
            # -----------------------------------------------------------------
            zone_data = [
                ('Refrigerated Storage', 'refrigerated', Decimal('2.00'), Decimal('8.00'), Decimal('30.00'), Decimal('65.00')),
                ('Frozen Storage', 'frozen', Decimal('-25.00'), Decimal('-18.00'), Decimal('20.00'), Decimal('50.00')),
                ('Ambient Storage', 'ambient', Decimal('15.00'), Decimal('25.00'), Decimal('30.00'), Decimal('70.00')),
                ('Deep Freeze Vault', 'deep_freeze', Decimal('-40.00'), Decimal('-30.00'), Decimal('15.00'), Decimal('40.00')),
                ('Ultra Cold Chamber', 'ultra_cold', Decimal('-80.00'), Decimal('-60.00'), Decimal('10.00'), Decimal('30.00')),
            ]
            zones_created = []

            for name, ztype, min_t, max_t, min_h, max_h in zone_data:
                zone = TemperatureZone(
                    tenant=tenant,
                    name=name,
                    zone_type=ztype,
                    status='active',
                    min_temperature=min_t,
                    max_temperature=max_t,
                    min_humidity=min_h,
                    max_humidity=max_h,
                    description=f'{name} zone maintained between {min_t} and {max_t} degrees Celsius.',
                    created_by=random.choice(users),
                )
                zone.save()
                zones_created.append(zone)

            self.stdout.write(f'  Created {len(zones_created)} temperature zones.')

            # -----------------------------------------------------------------
            # 2. Temperature Sensors (6) with Readings
            # -----------------------------------------------------------------
            sensor_data = [
                ('Warehouse Thermocouple A', 'thermocouple', 'warehouse', 'Omega', 'TC-K200', 'active'),
                ('Cold Room RTD Probe', 'rtd', 'cold_room', 'Fluke', 'RTD-100', 'active'),
                ('Truck Data Logger #1', 'data_logger', 'truck', 'Testo', 'DL-174T', 'active'),
                ('Freezer Thermistor B', 'thermistor', 'freezer', 'Honeywell', 'TH-500', 'active'),
                ('Container IR Sensor', 'infrared', 'container', 'Flir', 'IR-E6X', 'offline'),
                ('Cold Room RTD Probe #2', 'rtd', 'cold_room', 'Emerson', 'RTD-250', 'maintenance'),
            ]
            # Map sensors to zones for realistic readings
            sensor_zone_map = [0, 0, 1, 1, 2, 3]  # index into zones_created
            sensors_created = []

            for i, (name, stype, loc, mfr, model, status) in enumerate(sensor_data):
                install_date = today - timedelta(days=random.randint(90, 730))
                calib_date = today - timedelta(days=random.randint(10, 180))
                sensor = TemperatureSensor(
                    tenant=tenant,
                    name=name,
                    sensor_type=stype,
                    location_type=loc,
                    status=status,
                    manufacturer=mfr,
                    model_number=model,
                    serial_number=f'SN-{random.randint(100000, 999999)}',
                    installation_date=install_date,
                    last_calibration_date=calib_date,
                    next_calibration_date=calib_date + timedelta(days=365),
                    calibration_interval_days=365,
                    location_description=f'{loc.replace("_", " ").title()} - Section {random.choice(["A", "B", "C"])}',
                    min_reading_range=zones_created[sensor_zone_map[i]].min_temperature - Decimal('10'),
                    max_reading_range=zones_created[sensor_zone_map[i]].max_temperature + Decimal('10'),
                    reading_interval_minutes=random.choice([5, 10, 15, 30]),
                    description=f'{name} installed for continuous temperature monitoring.',
                    created_by=random.choice(users),
                )
                sensor.save()
                sensors_created.append(sensor)

                # Readings (3-5 per sensor)
                zone = zones_created[sensor_zone_map[i]]
                min_t = float(zone.min_temperature)
                max_t = float(zone.max_temperature)
                num_readings = random.randint(3, 5)
                for j in range(num_readings):
                    temp = round(random.uniform(min_t - 1, max_t + 1), 2)
                    within = min_t <= temp <= max_t
                    TemperatureReading.objects.create(
                        sensor=sensor,
                        temperature=Decimal(str(temp)),
                        humidity=Decimal(str(round(random.uniform(20, 70), 2))),
                        recorded_at=now - timedelta(hours=random.randint(1, 168)),
                        is_within_range=within,
                        notes='' if within else 'Temperature outside expected range.',
                    )

            self.stdout.write(f'  Created {len(sensors_created)} sensors with temperature readings.')

            # -----------------------------------------------------------------
            # 3. Temperature Excursions (4)
            # -----------------------------------------------------------------
            excursion_data = [
                ('minor', 'detected', sensors_created[0], zones_created[0], Decimal('9.50'), Decimal('2.00'), Decimal('8.00'), 15, 12),
                ('major', 'detected', sensors_created[3], zones_created[1], Decimal('-15.00'), Decimal('-25.00'), Decimal('-18.00'), 45, 80),
                ('moderate', 'investigating', sensors_created[1], zones_created[0], Decimal('10.20'), Decimal('2.00'), Decimal('8.00'), 30, 25),
                ('critical', 'resolved', sensors_created[4], zones_created[2], Decimal('32.00'), Decimal('15.00'), Decimal('25.00'), 90, 150),
            ]
            excursions_created = []

            for severity, status, sensor, zone, temp_rec, exp_min, exp_max, duration, items_count in excursion_data:
                detected = now - timedelta(hours=random.randint(2, 120))
                exc = TemperatureExcursion(
                    tenant=tenant,
                    sensor=sensor,
                    zone=zone,
                    severity=severity,
                    status=status,
                    detected_at=detected,
                    acknowledged_at=detected + timedelta(minutes=random.randint(5, 30)) if status != 'detected' else None,
                    resolved_at=detected + timedelta(hours=random.randint(2, 24)) if status == 'resolved' else None,
                    temperature_recorded=temp_rec,
                    expected_min=exp_min,
                    expected_max=exp_max,
                    duration_minutes=duration,
                    affected_items_count=items_count,
                    impact_description=f'Temperature excursion of {severity} severity detected. {items_count} items potentially affected.',
                    corrective_action='Cooling system repaired and temperature restored to normal range.' if status == 'resolved' else '',
                    resolved_by=random.choice(users) if status == 'resolved' else None,
                    created_by=random.choice(users),
                )
                exc.save()
                excursions_created.append(exc)

            self.stdout.write(f'  Created {len(excursions_created)} temperature excursions.')

            # -----------------------------------------------------------------
            # 4. Cold Storage Units (5) with Items
            # -----------------------------------------------------------------
            unit_data = [
                ('Walk-in Cooler A', 'walk_in_cooler', 'active', zones_created[0], Decimal('120.00'), Decimal('4.50'), Decimal('45.00')),
                ('Walk-in Freezer B', 'walk_in_freezer', 'active', zones_created[1], Decimal('80.00'), Decimal('-20.00'), Decimal('35.00')),
                ('Blast Freezer #1', 'blast_freezer', 'active', zones_created[3], Decimal('25.00'), Decimal('-35.00'), Decimal('20.00')),
                ('Reach-in Refrigerator C', 'reach_in_refrigerator', 'draft', zones_created[0], Decimal('5.50'), None, None),
                ('Ultra-Low Freezer D', 'ultra_low_freezer', 'maintenance', zones_created[4], Decimal('15.00'), Decimal('-70.00'), Decimal('15.00')),
            ]
            units_created = []

            for name, utype, status, zone, capacity, curr_temp, curr_hum in unit_data:
                unit = ColdStorageUnit(
                    tenant=tenant,
                    name=name,
                    unit_type=utype,
                    status=status,
                    zone=zone,
                    capacity_cubic_meters=capacity,
                    current_temperature=curr_temp,
                    current_humidity=curr_hum,
                    location=random.choice(['Warehouse A', 'Warehouse B', 'Distribution Center', 'Loading Dock']),
                    manufacturer=random.choice(['Carrier', 'Thermo King', 'Daikin', 'Bitzer']),
                    model_number=f'CS-{random.randint(100, 999)}',
                    serial_number=f'SN-{random.randint(100000, 999999)}',
                    installation_date=today - timedelta(days=random.randint(180, 1095)),
                    description=f'{name} used for cold chain storage operations.',
                    created_by=random.choice(users),
                )
                unit.save()
                units_created.append(unit)

                # Cold Storage Items (2-3 per unit)
                item_pool = [
                    ('Insulin Vials', 'PHARM', 'vials', Decimal('2.00'), Decimal('8.00')),
                    ('Flu Vaccine Batch', 'VAX', 'doses', Decimal('2.00'), Decimal('8.00')),
                    ('Frozen Plasma Units', 'BLOOD', 'units', Decimal('-25.00'), Decimal('-18.00')),
                    ('Fresh Produce Crate', 'FOOD', 'kg', Decimal('1.00'), Decimal('5.00')),
                    ('Dairy Products', 'DAIRY', 'liters', Decimal('2.00'), Decimal('6.00')),
                    ('Frozen Seafood Pallet', 'SEAFD', 'kg', Decimal('-22.00'), Decimal('-18.00')),
                    ('Biological Samples', 'BIO', 'units', Decimal('-80.00'), Decimal('-60.00')),
                    ('mRNA Reagents', 'CHEM', 'vials', Decimal('-30.00'), Decimal('-20.00')),
                    ('Ice Cream Bulk', 'FOOD', 'kg', Decimal('-25.00'), Decimal('-18.00')),
                    ('Fresh Meat Cuts', 'MEAT', 'kg', Decimal('0.00'), Decimal('4.00')),
                ]
                conditions = ['good', 'good', 'good', 'near_expiry']
                for item_name, batch_prefix, uom, temp_min, temp_max in random.sample(item_pool, random.randint(2, 3)):
                    ColdStorageItem.objects.create(
                        storage_unit=unit,
                        item_name=item_name,
                        batch_number=f'{batch_prefix}-{random.randint(10000, 99999)}',
                        lot_number=f'LOT-{random.randint(1000, 9999)}',
                        condition=random.choice(conditions),
                        quantity=Decimal(str(random.randint(10, 500))),
                        unit_of_measure=uom,
                        storage_date=today - timedelta(days=random.randint(1, 60)),
                        expiry_date=today + timedelta(days=random.randint(30, 365)),
                        temperature_requirement_min=temp_min,
                        temperature_requirement_max=temp_max,
                        notes=f'Stored in {unit.name}.',
                    )

            self.stdout.write(f'  Created {len(units_created)} cold storage units with items.')

            # -----------------------------------------------------------------
            # 5. Compliance Reports (3) with Items
            # -----------------------------------------------------------------
            report_data = [
                ('Monthly Temperature Log - January', 'temperature_log', 'draft', 'fda'),
                ('Q4 Excursion Summary Report', 'excursion_summary', 'generated', 'haccp'),
                ('Annual Storage Audit 2025', 'storage_audit', 'approved', 'gmp'),
            ]
            reports_created = []

            for title, rtype, status, reg_body in report_data:
                period_start = today - timedelta(days=random.randint(30, 90))
                report = ComplianceReport(
                    tenant=tenant,
                    title=title,
                    report_type=rtype,
                    status=status,
                    period_start=period_start,
                    period_end=period_start + timedelta(days=30),
                    regulatory_body=reg_body,
                    findings_summary=f'Summary of findings for {title}.',
                    recommendations='Continue monitoring. Review calibration schedules.' if status != 'draft' else '',
                    approved_by=random.choice(users) if status == 'approved' else None,
                    approved_at=now - timedelta(days=random.randint(1, 10)) if status == 'approved' else None,
                    created_by=random.choice(users),
                )
                report.save()
                reports_created.append(report)

                # Compliance Report Items (3-4 per report)
                param_pool = [
                    ('Average Storage Temperature', '2-8 deg C', '4.5', 'deg C', 'pass'),
                    ('Max Temperature Excursion', '< 10 deg C', '9.2', 'deg C', 'warning'),
                    ('Sensor Calibration Status', 'All calibrated', '5/6 calibrated', '', 'warning'),
                    ('Cold Room Humidity', '30-65% RH', '42.3', '% RH', 'pass'),
                    ('Excursion Response Time', '< 30 min', '18', 'min', 'pass'),
                    ('Backup Power Test', 'Functional', 'Passed', '', 'pass'),
                    ('Door Seal Integrity', 'No gaps', 'Minor gap unit 3', '', 'fail'),
                    ('Temperature Uniformity', '+/- 2 deg C', '1.8', 'deg C', 'pass'),
                ]
                for param, spec, value, uom, result in random.sample(param_pool, random.randint(3, 4)):
                    ComplianceReportItem.objects.create(
                        report=report,
                        parameter_name=param,
                        specification=spec,
                        measured_value=value,
                        unit_of_measure=uom,
                        result=result if status != 'draft' else 'not_tested',
                        notes='',
                    )

            self.stdout.write(f'  Created {len(reports_created)} compliance reports with items.')

            # -----------------------------------------------------------------
            # 6. Reefer Units (4)
            # -----------------------------------------------------------------
            reefer_data = [
                ('Reefer Container Alpha', 'reefer_container', 'active', 'r404a', 'Carrier', 'ThinLine', Decimal('-20.00'), 45000),
                ('Refrigerated Truck #1', 'refrigerated_truck', 'active', 'r134a', 'Thermo King', 'V-520', Decimal('4.00'), 32000),
                ('Cold Room Unit C', 'cold_room', 'active', 'r410a', 'Daikin', 'CR-800', Decimal('-2.00'), 28000),
                ('Transport Cooler T4', 'transport_cooler', 'draft', 'r290', 'Zanotti', 'Z380', Decimal('5.00'), 12000),
            ]
            reefers_created = []

            for name, rtype, status, refrig, mfr, model, set_temp, cost in reefer_data:
                purchase = today - timedelta(days=random.randint(180, 1095))
                last_svc = today - timedelta(days=random.randint(10, 90))
                reefer = ReeferUnit(
                    tenant=tenant,
                    name=name,
                    unit_type=rtype,
                    status=status,
                    refrigerant_type=refrig,
                    manufacturer=mfr,
                    model_number=model,
                    serial_number=f'SN-{random.randint(100000, 999999)}',
                    purchase_date=purchase,
                    purchase_cost=Decimal(str(cost)),
                    currency='USD',
                    last_service_date=last_svc,
                    next_service_date=last_svc + timedelta(days=90),
                    set_temperature=set_temp,
                    location=random.choice(['Yard A', 'Yard B', 'Loading Bay 1', 'Distribution Hub']),
                    description=f'{name} for cold chain transport and storage.',
                    created_by=random.choice(users),
                )
                reefer.save()
                reefers_created.append(reefer)

            self.stdout.write(f'  Created {len(reefers_created)} reefer units.')

            # -----------------------------------------------------------------
            # 7. Reefer Maintenance (5)
            # -----------------------------------------------------------------
            maint_data = [
                ('Routine Inspection - Reefer Alpha', 'routine_inspection', 'medium', 'monthly', 'draft', 500, 0),
                ('Compressor Service - Truck #1', 'compressor_service', 'high', 'quarterly', 'scheduled', 1200, 0),
                ('Refrigerant Level Check', 'refrigerant_check', 'low', 'semi_annual', 'in_progress', 300, 250),
                ('Thermostat Calibration - Cold Room', 'thermostat_calibration', 'medium', 'annual', 'completed', 400, 380),
                ('Emergency Compressor Repair', 'emergency_repair', 'urgent', 'one_time', 'completed', 3000, 3500),
            ]
            maints_created = []

            for i, (title, mtype, priority, freq, status, est_cost, act_cost) in enumerate(maint_data):
                reefer = reefers_created[i % len(reefers_created)]
                sched_date = today + timedelta(days=random.randint(-15, 30))
                maint = ReeferMaintenance(
                    tenant=tenant,
                    reefer=reefer,
                    maintenance_type=mtype,
                    priority=priority,
                    frequency=freq,
                    status=status,
                    title=title,
                    description=f'{title} for {reefer.name}.',
                    scheduled_date=sched_date,
                    completed_date=sched_date - timedelta(days=random.randint(0, 5)) if status == 'completed' else None,
                    assigned_to=random.choice(users),
                    estimated_cost=Decimal(str(est_cost)),
                    actual_cost=Decimal(str(act_cost)),
                    currency='USD',
                    findings='All components within normal operating parameters.' if status == 'completed' else '',
                    next_due_date=sched_date + timedelta(days=random.randint(30, 180)),
                    created_by=random.choice(users),
                )
                maint.save()
                maints_created.append(maint)

            self.stdout.write(f'  Created {len(maints_created)} reefer maintenance records.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Cold Chain Management data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'NOTE: Superuser "admin" has no tenant — '
            'data won\'t appear when logged in as admin. '
            'Use a tenant admin account (e.g., admin_<slug>) to see the data.'
        ))
