from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# ASSET REGISTRY
# =============================================================================

class Asset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('truck', 'Truck'),
        ('forklift', 'Forklift'),
        ('machinery', 'Machinery'),
        ('conveyor', 'Conveyor System'),
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('computer', 'Computer/IT'),
        ('furniture', 'Furniture'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('in_maintenance', 'In Maintenance'),
        ('out_of_service', 'Out of Service'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='assets',
    )
    asset_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    asset_type = models.CharField(
        max_length=20, choices=ASSET_TYPE_CHOICES, default='equipment',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    condition = models.CharField(
        max_length=10, choices=CONDITION_CHOICES, default='good',
    )
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(blank=True, null=True)
    purchase_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3,
        choices=[
            ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
            ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
        ],
        default='USD',
    )
    warranty_expiry = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_assets',
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_assets',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        unique_together = ('tenant', 'asset_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.asset_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.asset_number:
            last = Asset.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.asset_number:
                try:
                    num = int(last.asset_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.asset_number = f"AST-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_warranty_active(self):
        if self.warranty_expiry:
            return timezone.now().date() <= self.warranty_expiry
        return False

    @property
    def age_in_days(self):
        if self.purchase_date:
            return (timezone.now().date() - self.purchase_date).days
        return 0

    @property
    def spec_count(self):
        return self.specifications.count()


class AssetSpecification(models.Model):
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='specifications',
    )
    spec_name = models.CharField(max_length=255)
    spec_value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.spec_name}: {self.spec_value}"


# =============================================================================
# PREVENTIVE MAINTENANCE
# =============================================================================

class PreventiveMaintenance(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='preventive_maintenance',
    )
    pm_number = models.CharField(max_length=50)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='preventive_schedules',
    )
    title = models.CharField(max_length=255)
    frequency = models.CharField(
        max_length=15, choices=FREQUENCY_CHOICES, default='monthly',
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    scheduled_date = models.DateField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    next_due_date = models.DateField(blank=True, null=True)
    estimated_duration_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
    )
    actual_duration_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
    )
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_pm',
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_pm',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preventive Maintenance'
        verbose_name_plural = 'Preventive Maintenance'
        unique_together = ('tenant', 'pm_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pm_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.pm_number:
            last = PreventiveMaintenance.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.pm_number:
                try:
                    num = int(last.pm_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.pm_number = f"PM-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.scheduled_date and self.status not in ('completed', 'cancelled'):
            return timezone.now().date() > self.scheduled_date
        return False

    @property
    def task_count(self):
        return self.tasks.count()


class MaintenanceTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    maintenance = models.ForeignKey(
        PreventiveMaintenance,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    task_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='pending',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.task_name} - {self.get_status_display()}"


# =============================================================================
# BREAKDOWN MAINTENANCE
# =============================================================================

class BreakdownMaintenance(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('assigned', 'Assigned'),
        ('diagnosing', 'Diagnosing'),
        ('repairing', 'Repairing'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='breakdown_maintenance',
    )
    bm_number = models.CharField(max_length=50)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='breakdowns',
    )
    title = models.CharField(max_length=255)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='moderate',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='reported')
    reported_date = models.DateTimeField(default=timezone.now)
    started_date = models.DateTimeField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    downtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    repair_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    root_cause = models.TextField(blank=True)
    repair_description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_breakdowns',
        blank=True,
        null=True,
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reported_breakdowns',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Breakdown Maintenance'
        verbose_name_plural = 'Breakdown Maintenance'
        unique_together = ('tenant', 'bm_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bm_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.bm_number:
            last = BreakdownMaintenance.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.bm_number:
                try:
                    num = int(last.bm_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.bm_number = f"BM-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def resolution_time_hours(self):
        if self.started_date and self.completed_date:
            delta = self.completed_date - self.started_date
            return round(delta.total_seconds() / 3600, 2)
        return 0


# =============================================================================
# SPARE PARTS INVENTORY
# =============================================================================

class SparePart(models.Model):
    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='spare_parts',
    )
    part_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    compatible_assets = models.ManyToManyField(
        Asset,
        related_name='compatible_spare_parts',
        blank=True,
    )
    quantity_on_hand = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    reorder_quantity = models.PositiveIntegerField(default=10)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3,
        choices=[
            ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
            ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
        ],
        default='USD',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_stock')
    location = models.CharField(max_length=255, blank=True)
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.SET_NULL,
        related_name='spare_parts',
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_spare_parts',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Spare Part'
        verbose_name_plural = 'Spare Parts'
        unique_together = ('tenant', 'part_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.part_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.part_number:
            last = SparePart.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.part_number:
                try:
                    num = int(last.part_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.part_number = f"SP-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        return self.quantity_on_hand * self.unit_cost

    @property
    def needs_reorder(self):
        return self.quantity_on_hand <= self.reorder_level

    @property
    def usage_count(self):
        return self.usages.count()


class SparePartUsage(models.Model):
    spare_part = models.ForeignKey(
        SparePart,
        on_delete=models.CASCADE,
        related_name='usages',
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        related_name='spare_part_usages',
        blank=True,
        null=True,
    )
    breakdown = models.ForeignKey(
        BreakdownMaintenance,
        on_delete=models.SET_NULL,
        related_name='parts_used',
        blank=True,
        null=True,
    )
    quantity_used = models.PositiveIntegerField(default=1)
    used_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-used_date']

    def __str__(self):
        return f"{self.spare_part.name} x {self.quantity_used}"


# =============================================================================
# ASSET DEPRECIATION
# =============================================================================

class AssetDepreciation(models.Model):
    METHOD_CHOICES = [
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('double_declining', 'Double Declining Balance'),
        ('sum_of_years', 'Sum of Years Digits'),
        ('units_of_production', 'Units of Production'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('fully_depreciated', 'Fully Depreciated'),
        ('disposed', 'Disposed'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='asset_depreciations',
    )
    depreciation_number = models.CharField(max_length=50)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='depreciations',
    )
    method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default='straight_line',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    original_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    salvage_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    useful_life_years = models.PositiveIntegerField(default=5)
    start_date = models.DateField(blank=True, null=True)
    annual_depreciation = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    accumulated_depreciation = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    current_book_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_depreciations',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Asset Depreciation'
        verbose_name_plural = 'Asset Depreciations'
        unique_together = ('tenant', 'depreciation_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.depreciation_number} - {self.asset.name}"

    def save(self, *args, **kwargs):
        if not self.depreciation_number:
            last = AssetDepreciation.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.depreciation_number:
                try:
                    num = int(last.depreciation_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.depreciation_number = f"DEP-{num:05d}"
        # Auto-calculate straight line depreciation
        if self.method == 'straight_line' and self.useful_life_years > 0:
            depreciable = self.original_cost - self.salvage_value
            self.annual_depreciation = round(depreciable / self.useful_life_years, 2)
        super().save(*args, **kwargs)

    @property
    def depreciation_percentage(self):
        if self.original_cost > 0:
            return round(
                (self.accumulated_depreciation / self.original_cost) * 100, 2
            )
        return 0

    @property
    def is_fully_depreciated(self):
        return self.current_book_value <= self.salvage_value
