from django.conf import settings
from django.db import models


# =============================================================================
# WORK CENTERS
# =============================================================================

class WorkCenter(models.Model):
    WORK_CENTER_TYPE_CHOICES = [
        ('machine', 'Machine'),
        ('assembly_line', 'Assembly Line'),
        ('manual_station', 'Manual Station'),
        ('testing_station', 'Testing Station'),
        ('packaging', 'Packaging'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='work_centers',
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    work_center_type = models.CharField(
        max_length=20, choices=WORK_CENTER_TYPE_CHOICES, default='machine',
    )
    hourly_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# BILL OF MATERIALS
# =============================================================================

class BillOfMaterials(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('obsolete', 'Obsolete'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='boms',
    )
    bom_number = models.CharField(max_length=50)
    product = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='boms',
    )
    version = models.CharField(max_length=20, default='1.0')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    yield_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_boms',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_boms',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bill of Materials'
        verbose_name_plural = 'Bills of Materials'
        unique_together = ('tenant', 'bom_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bom_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.bom_number:
            last = BillOfMaterials.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.bom_number:
                try:
                    num = int(last.bom_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.bom_number = f"BOM-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_component_cost(self):
        return sum(
            (line.quantity * (line.item.unit_price if line.item else 0))
            for line in self.items.all()
        )

    @property
    def unit_cost(self):
        if self.yield_quantity and self.yield_quantity > 0:
            return self.total_component_cost / self.yield_quantity
        return self.total_component_cost


class BOMLineItem(models.Model):
    UOM_CHOICES = [
        ('piece', 'Piece'), ('kg', 'Kilogram'), ('g', 'Gram'),
        ('liter', 'Liter'), ('ml', 'Milliliter'), ('meter', 'Meter'),
        ('cm', 'Centimeter'), ('box', 'Box'), ('pack', 'Pack'),
        ('set', 'Set'), ('hour', 'Hour'), ('day', 'Day'), ('unit', 'Unit'),
    ]

    bom = models.ForeignKey(
        BillOfMaterials,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='bom_line_items',
        blank=True,
        null=True,
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_of_measure = models.CharField(
        max_length=20, choices=UOM_CHOICES, default='piece',
    )
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name if self.item else 'N/A'} x {self.quantity}"

    @property
    def effective_quantity(self):
        return self.quantity * (1 + self.scrap_percentage / 100)


# =============================================================================
# PRODUCTION SCHEDULING
# =============================================================================

class ProductionSchedule(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='production_schedules',
    )
    schedule_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_production_schedules',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'schedule_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.schedule_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.schedule_number:
            last = ProductionSchedule.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.schedule_number:
                try:
                    num = int(last.schedule_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.schedule_number = f"PS-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_planned_quantity(self):
        return sum(item.planned_quantity for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class ProductionScheduleItem(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    schedule = models.ForeignKey(
        ProductionSchedule,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='schedule_items',
        blank=True,
        null=True,
    )
    bom = models.ForeignKey(
        BillOfMaterials,
        on_delete=models.SET_NULL,
        related_name='schedule_items',
        blank=True,
        null=True,
    )
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    work_center = models.ForeignKey(
        WorkCenter,
        on_delete=models.SET_NULL,
        related_name='schedule_items',
        blank=True,
        null=True,
    )
    planned_start = models.DateTimeField(blank=True, null=True)
    planned_end = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['planned_start', 'id']

    def __str__(self):
        product_name = self.product.name if self.product else 'N/A'
        return f"{product_name} x {self.planned_quantity}"


# =============================================================================
# WORK ORDER MANAGEMENT
# =============================================================================

class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('released', 'Released'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='work_orders',
    )
    work_order_number = models.CharField(max_length=50)
    product = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='work_orders',
    )
    bom = models.ForeignKey(
        BillOfMaterials,
        on_delete=models.SET_NULL,
        related_name='work_orders',
        blank=True,
        null=True,
    )
    schedule = models.ForeignKey(
        ProductionSchedule,
        on_delete=models.SET_NULL,
        related_name='work_orders',
        blank=True,
        null=True,
    )
    work_center = models.ForeignKey(
        WorkCenter,
        on_delete=models.SET_NULL,
        related_name='work_orders',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    completed_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    scrap_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    planned_start_date = models.DateField(blank=True, null=True)
    planned_end_date = models.DateField(blank=True, null=True)
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_work_orders',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'work_order_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.work_order_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.work_order_number:
            last = WorkOrder.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.work_order_number:
                try:
                    num = int(last.work_order_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.work_order_number = f"WO-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def completion_percentage(self):
        if self.planned_quantity and self.planned_quantity > 0:
            return round((self.completed_quantity / self.planned_quantity) * 100, 1)
        return 0

    @property
    def scrap_rate(self):
        total = self.completed_quantity + self.scrap_quantity
        if total > 0:
            return round((self.scrap_quantity / total) * 100, 1)
        return 0

    @property
    def remaining_quantity(self):
        return max(self.planned_quantity - self.completed_quantity, 0)


class WorkOrderOperation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='operations',
    )
    sequence = models.PositiveIntegerField(default=10)
    name = models.CharField(max_length=255)
    work_center = models.ForeignKey(
        WorkCenter,
        on_delete=models.SET_NULL,
        related_name='operations',
        blank=True,
        null=True,
    )
    planned_duration_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    actual_duration_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['sequence', 'id']

    def __str__(self):
        return f"Op {self.sequence}: {self.name}"

    @property
    def efficiency(self):
        if self.planned_duration_hours and self.planned_duration_hours > 0 and self.actual_duration_hours > 0:
            return round((self.planned_duration_hours / self.actual_duration_hours) * 100, 1)
        return 0


# =============================================================================
# MATERIAL RESOURCE PLANNING (MRP)
# =============================================================================

class MRPRun(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='mrp_runs',
    )
    mrp_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    run_date = models.DateField(blank=True, null=True)
    planning_horizon_days = models.PositiveIntegerField(default=30)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_mrp_runs',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'MRP Run'
        verbose_name_plural = 'MRP Runs'
        unique_together = ('tenant', 'mrp_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mrp_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.mrp_number:
            last = MRPRun.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.mrp_number:
                try:
                    num = int(last.mrp_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.mrp_number = f"MRP-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_requirements(self):
        return self.requirements.count()

    @property
    def total_net_requirement_value(self):
        return sum(
            r.net_requirement * (r.item.unit_price if r.item else 0)
            for r in self.requirements.all()
        )


class MRPRequirement(models.Model):
    mrp_run = models.ForeignKey(
        MRPRun,
        on_delete=models.CASCADE,
        related_name='requirements',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='mrp_requirements',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        related_name='mrp_requirements',
        blank=True,
        null=True,
    )
    required_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    on_hand_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    on_order_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_requirement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    planned_order_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['item__name']

    def __str__(self):
        return f"{self.item.name} - Net: {self.net_requirement}"


# =============================================================================
# SHOP FLOOR CONTROL
# =============================================================================

class ProductionLog(models.Model):
    LOG_TYPE_CHOICES = [
        ('production', 'Production'),
        ('downtime', 'Downtime'),
        ('setup', 'Setup'),
        ('maintenance', 'Maintenance'),
        ('quality_check', 'Quality Check'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='production_logs',
    )
    log_number = models.CharField(max_length=50)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='production_logs',
    )
    operation = models.ForeignKey(
        WorkOrderOperation,
        on_delete=models.SET_NULL,
        related_name='production_logs',
        blank=True,
        null=True,
    )
    work_center = models.ForeignKey(
        WorkCenter,
        on_delete=models.SET_NULL,
        related_name='production_logs',
        blank=True,
        null=True,
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='production_logs',
        blank=True,
        null=True,
    )
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES, default='production')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    quantity_produced = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_rejected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'log_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.log_number} - {self.get_log_type_display()}"

    def save(self, *args, **kwargs):
        if not self.log_number:
            last = ProductionLog.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.log_number:
                try:
                    num = int(last.log_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.log_number = f"PL-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return 0

    @property
    def yield_rate(self):
        total = self.quantity_produced + self.quantity_rejected
        if total > 0:
            return round((self.quantity_produced / total) * 100, 1)
        return 0
