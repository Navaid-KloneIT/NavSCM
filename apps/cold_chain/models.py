from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# TEMPERATURE SENSOR REGISTRY
# =============================================================================

class TemperatureSensor(models.Model):
    SENSOR_TYPE_CHOICES = [
        ('thermocouple', 'Thermocouple'),
        ('rtd', 'RTD'),
        ('thermistor', 'Thermistor'),
        ('infrared', 'Infrared'),
        ('data_logger', 'Data Logger'),
    ]

    LOCATION_TYPE_CHOICES = [
        ('warehouse', 'Warehouse'),
        ('truck', 'Truck'),
        ('container', 'Container'),
        ('cold_room', 'Cold Room'),
        ('freezer', 'Freezer'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='temperature_sensors',
    )
    sensor_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    sensor_type = models.CharField(
        max_length=20, choices=SENSOR_TYPE_CHOICES, default='thermocouple',
    )
    location_type = models.CharField(
        max_length=20, choices=LOCATION_TYPE_CHOICES, default='warehouse',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    installation_date = models.DateField(blank=True, null=True)
    last_calibration_date = models.DateField(blank=True, null=True)
    next_calibration_date = models.DateField(blank=True, null=True)
    calibration_interval_days = models.PositiveIntegerField(default=365)
    location_description = models.CharField(max_length=255, blank=True)
    min_reading_range = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
    )
    max_reading_range = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
    )
    reading_interval_minutes = models.PositiveIntegerField(default=15)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_temperature_sensors',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Temperature Sensor'
        verbose_name_plural = 'Temperature Sensors'
        unique_together = ('tenant', 'sensor_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sensor_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.sensor_number:
            last = TemperatureSensor.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.sensor_number:
                try:
                    num = int(last.sensor_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.sensor_number = f"SNR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_calibration_due(self):
        if self.next_calibration_date:
            return timezone.now().date() >= self.next_calibration_date
        return False

    @property
    def reading_count(self):
        return self.readings.count()


class TemperatureReading(models.Model):
    sensor = models.ForeignKey(
        TemperatureSensor,
        on_delete=models.CASCADE,
        related_name='readings',
    )
    temperature = models.DecimalField(max_digits=6, decimal_places=2)
    humidity = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
    )
    recorded_at = models.DateTimeField()
    is_within_range = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.sensor} - {self.temperature}°C at {self.recorded_at}"


# =============================================================================
# TEMPERATURE ZONE
# =============================================================================

class TemperatureZone(models.Model):
    ZONE_TYPE_CHOICES = [
        ('refrigerated', 'Refrigerated'),
        ('frozen', 'Frozen'),
        ('ambient', 'Ambient'),
        ('deep_freeze', 'Deep Freeze'),
        ('ultra_cold', 'Ultra Cold'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='temperature_zones',
    )
    zone_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    zone_type = models.CharField(
        max_length=20, choices=ZONE_TYPE_CHOICES, default='refrigerated',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    min_temperature = models.DecimalField(max_digits=6, decimal_places=2)
    max_temperature = models.DecimalField(max_digits=6, decimal_places=2)
    min_humidity = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
    )
    max_humidity = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_temperature_zones',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Temperature Zone'
        verbose_name_plural = 'Temperature Zones'
        unique_together = ('tenant', 'zone_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.zone_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.zone_number:
            last = TemperatureZone.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.zone_number:
                try:
                    num = int(last.zone_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.zone_number = f"ZN-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def temperature_range_display(self):
        return f"{self.min_temperature}°C to {self.max_temperature}°C"


# =============================================================================
# TEMPERATURE EXCURSION
# =============================================================================

class TemperatureExcursion(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='temperature_excursions',
    )
    excursion_number = models.CharField(max_length=50)
    sensor = models.ForeignKey(
        TemperatureSensor,
        on_delete=models.SET_NULL,
        related_name='excursions',
        blank=True,
        null=True,
    )
    zone = models.ForeignKey(
        TemperatureZone,
        on_delete=models.SET_NULL,
        related_name='excursions',
        blank=True,
        null=True,
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='moderate',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='detected')
    detected_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    temperature_recorded = models.DecimalField(max_digits=6, decimal_places=2)
    expected_min = models.DecimalField(max_digits=6, decimal_places=2)
    expected_max = models.DecimalField(max_digits=6, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=0)
    affected_items_count = models.PositiveIntegerField(default=0)
    impact_description = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='resolved_excursions',
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_excursions',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Temperature Excursion'
        verbose_name_plural = 'Temperature Excursions'
        unique_together = ('tenant', 'excursion_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.excursion_number} - {self.get_severity_display()}"

    def save(self, *args, **kwargs):
        if not self.excursion_number:
            last = TemperatureExcursion.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.excursion_number:
                try:
                    num = int(last.excursion_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.excursion_number = f"EXC-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# COLD STORAGE UNIT
# =============================================================================

class ColdStorageUnit(models.Model):
    UNIT_TYPE_CHOICES = [
        ('walk_in_cooler', 'Walk-in Cooler'),
        ('walk_in_freezer', 'Walk-in Freezer'),
        ('reach_in_refrigerator', 'Reach-in Refrigerator'),
        ('blast_freezer', 'Blast Freezer'),
        ('ultra_low_freezer', 'Ultra-Low Freezer'),
        ('refrigerated_container', 'Refrigerated Container'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('out_of_service', 'Out of Service'),
        ('retired', 'Retired'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='cold_storage_units',
    )
    unit_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    unit_type = models.CharField(
        max_length=25, choices=UNIT_TYPE_CHOICES, default='walk_in_cooler',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    zone = models.ForeignKey(
        TemperatureZone,
        on_delete=models.SET_NULL,
        related_name='storage_units',
        blank=True,
        null=True,
    )
    capacity_cubic_meters = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    current_temperature = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
    )
    current_humidity = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
    )
    location = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    installation_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_cold_storage_units',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cold Storage Unit'
        verbose_name_plural = 'Cold Storage Units'
        unique_together = ('tenant', 'unit_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.unit_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.unit_number:
            last = ColdStorageUnit.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.unit_number:
                try:
                    num = int(last.unit_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.unit_number = f"CSU-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()

    @property
    def is_temperature_normal(self):
        if self.zone and self.current_temperature is not None:
            return self.zone.min_temperature <= self.current_temperature <= self.zone.max_temperature
        return True


class ColdStorageItem(models.Model):
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('near_expiry', 'Near Expiry'),
        ('expired', 'Expired'),
        ('compromised', 'Compromised'),
    ]

    storage_unit = models.ForeignKey(
        ColdStorageUnit,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item_name = models.CharField(max_length=255)
    batch_number = models.CharField(max_length=100, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    condition = models.CharField(
        max_length=15, choices=CONDITION_CHOICES, default='good',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_of_measure = models.CharField(max_length=50, default='units')
    storage_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    temperature_requirement_min = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
    )
    temperature_requirement_max = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.item_name} - Batch: {self.batch_number}"

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False


# =============================================================================
# COMPLIANCE REPORT
# =============================================================================

class ComplianceReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('temperature_log', 'Temperature Log'),
        ('excursion_summary', 'Excursion Summary'),
        ('storage_audit', 'Storage Audit'),
        ('equipment_qualification', 'Equipment Qualification'),
        ('regulatory_filing', 'Regulatory Filing'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ]

    REGULATORY_BODY_CHOICES = [
        ('fda', 'FDA'),
        ('ema', 'EMA'),
        ('who', 'WHO'),
        ('haccp', 'HACCP'),
        ('gmp', 'GMP'),
        ('iso', 'ISO'),
        ('custom', 'Custom'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='compliance_reports',
    )
    report_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    report_type = models.CharField(
        max_length=25, choices=REPORT_TYPE_CHOICES, default='temperature_log',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    period_start = models.DateField()
    period_end = models.DateField()
    regulatory_body = models.CharField(
        max_length=10, choices=REGULATORY_BODY_CHOICES, default='haccp',
    )
    findings_summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_cc_reports',
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_compliance_reports',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compliance Report'
        verbose_name_plural = 'Compliance Reports'
        unique_together = ('tenant', 'report_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            last = ComplianceReport.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.report_number:
                try:
                    num = int(last.report_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.report_number = f"CCR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()

    @property
    def is_all_passed(self):
        return self.items.exists() and not self.items.exclude(result='pass').exists()


class ComplianceReportItem(models.Model):
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning'),
        ('not_tested', 'Not Tested'),
    ]

    report = models.ForeignKey(
        ComplianceReport,
        on_delete=models.CASCADE,
        related_name='items',
    )
    parameter_name = models.CharField(max_length=255)
    specification = models.CharField(max_length=255, blank=True)
    measured_value = models.CharField(max_length=255)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    result = models.CharField(
        max_length=15, choices=RESULT_CHOICES, default='not_tested',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.parameter_name}: {self.result}"


# =============================================================================
# REEFER UNIT REGISTRY
# =============================================================================

class ReeferUnit(models.Model):
    UNIT_TYPE_CHOICES = [
        ('reefer_container', 'Reefer Container'),
        ('refrigerated_truck', 'Refrigerated Truck'),
        ('cold_room', 'Cold Room'),
        ('display_case', 'Display Case'),
        ('transport_cooler', 'Transport Cooler'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('out_of_service', 'Out of Service'),
        ('retired', 'Retired'),
    ]

    REFRIGERANT_TYPE_CHOICES = [
        ('r134a', 'R-134a'),
        ('r404a', 'R-404A'),
        ('r410a', 'R-410A'),
        ('r290', 'R-290'),
        ('r744', 'R-744'),
        ('ammonia', 'Ammonia'),
        ('other', 'Other'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='reefer_units',
    )
    unit_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    unit_type = models.CharField(
        max_length=20, choices=UNIT_TYPE_CHOICES, default='reefer_container',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    refrigerant_type = models.CharField(
        max_length=10, choices=REFRIGERANT_TYPE_CHOICES, default='r134a',
    )
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(blank=True, null=True)
    purchase_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    last_service_date = models.DateField(blank=True, null=True)
    next_service_date = models.DateField(blank=True, null=True)
    set_temperature = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
    )
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_reefer_units',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reefer Unit'
        verbose_name_plural = 'Reefer Units'
        unique_together = ('tenant', 'unit_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.unit_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.unit_number:
            last = ReeferUnit.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.unit_number:
                try:
                    num = int(last.unit_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.unit_number = f"RFR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_service_due(self):
        if self.next_service_date:
            return timezone.now().date() >= self.next_service_date
        return False

    @property
    def maintenance_count(self):
        return self.maintenances.count()


# =============================================================================
# REEFER MAINTENANCE
# =============================================================================

class ReeferMaintenance(models.Model):
    MAINTENANCE_TYPE_CHOICES = [
        ('routine_inspection', 'Routine Inspection'),
        ('compressor_service', 'Compressor Service'),
        ('refrigerant_check', 'Refrigerant Check'),
        ('thermostat_calibration', 'Thermostat Calibration'),
        ('defrost_cycle', 'Defrost Cycle'),
        ('emergency_repair', 'Emergency Repair'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    FREQUENCY_CHOICES = [
        ('one_time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='reefer_maintenance',
    )
    maintenance_number = models.CharField(max_length=50)
    reefer = models.ForeignKey(
        ReeferUnit,
        on_delete=models.CASCADE,
        related_name='maintenances',
    )
    maintenance_type = models.CharField(
        max_length=25, choices=MAINTENANCE_TYPE_CHOICES, default='routine_inspection',
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium',
    )
    frequency = models.CharField(
        max_length=15, choices=FREQUENCY_CHOICES, default='monthly',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scheduled_date = models.DateField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_reefer_maintenance',
        blank=True,
        null=True,
    )
    estimated_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    findings = models.TextField(blank=True)
    next_due_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_reefer_maintenance',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reefer Maintenance'
        verbose_name_plural = 'Reefer Maintenance'
        unique_together = ('tenant', 'maintenance_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.maintenance_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.maintenance_number:
            last = ReeferMaintenance.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.maintenance_number:
                try:
                    num = int(last.maintenance_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.maintenance_number = f"RFM-{num:05d}"
        super().save(*args, **kwargs)
