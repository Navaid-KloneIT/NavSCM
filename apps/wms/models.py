from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# BIN / LOCATION MANAGEMENT
# =============================================================================

class Bin(models.Model):
    BIN_TYPE_CHOICES = [
        ('bulk', 'Bulk Storage'),
        ('pick', 'Pick Location'),
        ('reserve', 'Reserve Storage'),
        ('staging', 'Staging Area'),
        ('dock', 'Dock Area'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='wms_bins',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='bins',
    )
    bin_code = models.CharField(max_length=50)
    zone = models.CharField(max_length=100, blank=True)
    aisle = models.CharField(max_length=50, blank=True)
    rack = models.CharField(max_length=50, blank=True)
    shelf = models.CharField(max_length=50, blank=True)
    bin_position = models.CharField(max_length=50, blank=True)
    bin_type = models.CharField(
        max_length=20, choices=BIN_TYPE_CHOICES, default='bulk',
    )
    capacity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_utilization = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'bin_code')
        ordering = ['warehouse', 'zone', 'aisle', 'rack', 'shelf']
        verbose_name_plural = 'Bins'

    def __str__(self):
        return f"{self.bin_code} ({self.warehouse.code})"

    def save(self, *args, **kwargs):
        if not self.bin_code:
            last = Bin.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.bin_code:
                try:
                    num = int(last.bin_code.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.bin_code = f"BIN-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def utilization_percentage(self):
        if self.capacity > 0:
            return round((self.current_utilization / self.capacity) * 100, 1)
        return 0


# =============================================================================
# INBOUND OPERATIONS
# =============================================================================

class DockAppointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('receiving', 'Receiving'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='dock_appointments',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='dock_appointments',
    )
    appointment_number = models.CharField(max_length=50)
    dock_number = models.CharField(max_length=50)
    appointment_date = models.DateField()
    time_slot = models.TimeField()
    carrier_name = models.CharField(max_length=255)
    trailer_number = models.CharField(max_length=100, blank=True)
    po_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'appointment_number')
        ordering = ['-appointment_date', '-time_slot']

    def __str__(self):
        return f"{self.appointment_number} - {self.carrier_name}"

    def save(self, *args, **kwargs):
        if not self.appointment_number:
            last = DockAppointment.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.appointment_number:
                try:
                    num = int(last.appointment_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.appointment_number = f"DOCK-{num:05d}"
        super().save(*args, **kwargs)


class ReceivingOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='receiving_orders',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='receiving_orders',
    )
    receiving_number = models.CharField(max_length=50)
    dock_appointment = models.ForeignKey(
        DockAppointment,
        on_delete=models.SET_NULL,
        related_name='receiving_orders',
        blank=True,
        null=True,
    )
    po_reference = models.CharField(max_length=100, blank=True)
    supplier_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='received_orders',
        blank=True,
        null=True,
    )
    received_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'receiving_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.receiving_number} - {self.supplier_name}"

    def save(self, *args, **kwargs):
        if not self.receiving_number:
            last = ReceivingOrder.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.receiving_number:
                try:
                    num = int(last.receiving_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.receiving_number = f"RCV-{num:05d}"
        super().save(*args, **kwargs)


class ReceivingOrderItem(models.Model):
    receiving_order = models.ForeignKey(
        ReceivingOrder,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='receiving_items',
    )
    expected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    damaged_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bin = models.ForeignKey(
        Bin,
        on_delete=models.SET_NULL,
        related_name='received_items',
        blank=True,
        null=True,
        help_text='Put-away destination bin.',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} x {self.expected_quantity}"


class PutAwayTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='putaway_tasks',
    )
    task_number = models.CharField(max_length=50)
    receiving_order = models.ForeignKey(
        ReceivingOrder,
        on_delete=models.CASCADE,
        related_name='putaway_tasks',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='putaway_tasks',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    source_bin = models.ForeignKey(
        Bin,
        on_delete=models.SET_NULL,
        related_name='putaway_source_tasks',
        blank=True,
        null=True,
    )
    destination_bin = models.ForeignKey(
        Bin,
        on_delete=models.SET_NULL,
        related_name='putaway_dest_tasks',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='putaway_tasks',
        blank=True,
        null=True,
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'task_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_number} - {self.item.name}"

    def save(self, *args, **kwargs):
        if not self.task_number:
            last = PutAwayTask.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.task_number:
                try:
                    num = int(last.task_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.task_number = f"PUT-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# OUTBOUND OPERATIONS
# =============================================================================

class PickList(models.Model):
    PICK_TYPE_CHOICES = [
        ('wave', 'Wave Pick'),
        ('batch', 'Batch Pick'),
        ('zone', 'Zone Pick'),
        ('single', 'Single Order'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
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
        related_name='pick_lists',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='pick_lists',
    )
    pick_number = models.CharField(max_length=50)
    pick_type = models.CharField(
        max_length=20, choices=PICK_TYPE_CHOICES, default='single',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_pick_lists',
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'pick_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pick_number}"

    def save(self, *args, **kwargs):
        if not self.pick_number:
            last = PickList.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.pick_number:
                try:
                    num = int(last.pick_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.pick_number = f"PICK-{num:05d}"
        super().save(*args, **kwargs)


class PickListItem(models.Model):
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked', 'Picked'),
        ('short', 'Short'),
        ('skipped', 'Skipped'),
    ]

    pick_list = models.ForeignKey(
        PickList,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='pick_list_items',
    )
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_picked = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    source_bin = models.ForeignKey(
        Bin,
        on_delete=models.SET_NULL,
        related_name='pick_list_items',
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20, choices=ITEM_STATUS_CHOICES, default='pending',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} x {self.quantity_requested}"


class PackingOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('packing', 'Packing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='packing_orders',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='packing_orders',
    )
    packing_number = models.CharField(max_length=50)
    pick_list = models.ForeignKey(
        PickList,
        on_delete=models.SET_NULL,
        related_name='packing_orders',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    packer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='packing_orders',
        blank=True,
        null=True,
    )
    packed_at = models.DateTimeField(blank=True, null=True)
    total_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_packages = models.PositiveIntegerField(default=0)
    shipping_method = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'packing_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.packing_number}"

    def save(self, *args, **kwargs):
        if not self.packing_number:
            last = PackingOrder.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.packing_number:
                try:
                    num = int(last.packing_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.packing_number = f"PACK-{num:05d}"
        super().save(*args, **kwargs)


class ShippingLabel(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='shipping_labels',
    )
    packing_order = models.ForeignKey(
        PackingOrder,
        on_delete=models.CASCADE,
        related_name='shipping_labels',
    )
    label_number = models.CharField(max_length=50)
    carrier = models.CharField(max_length=255)
    tracking_number = models.CharField(max_length=255, blank=True)
    destination_address = models.TextField()
    weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dimensions = models.CharField(max_length=100, blank=True)
    label_data = models.TextField(blank=True, help_text='Encoded label data for printing.')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'label_number')
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.label_number} - {self.carrier}"

    def save(self, *args, **kwargs):
        if not self.label_number:
            last = ShippingLabel.objects.filter(
                tenant=self.tenant
            ).order_by('-generated_at').first()
            if last and last.label_number:
                try:
                    num = int(last.label_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.label_number = f"SHP-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# CYCLE COUNTING
# =============================================================================

class CycleCountPlan(models.Model):
    COUNT_TYPE_CHOICES = [
        ('abc', 'ABC Analysis'),
        ('location', 'Location-based'),
        ('random', 'Random Sample'),
        ('full', 'Full Count'),
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='cycle_count_plans',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='cycle_count_plans',
    )
    plan_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    count_type = models.CharField(
        max_length=20, choices=COUNT_TYPE_CHOICES, default='abc',
    )
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default='monthly',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    next_count_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'plan_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.plan_number:
            last = CycleCountPlan.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.plan_number:
                try:
                    num = int(last.plan_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.plan_number = f"CCP-{num:05d}"
        super().save(*args, **kwargs)


class CycleCount(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='cycle_counts',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='cycle_counts',
    )
    count_number = models.CharField(max_length=50)
    plan = models.ForeignKey(
        CycleCountPlan,
        on_delete=models.SET_NULL,
        related_name='cycle_counts',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    counter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='cycle_counts',
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    total_items = models.PositiveIntegerField(default=0)
    items_counted = models.PositiveIntegerField(default=0)
    variance_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'count_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.count_number}"

    def save(self, *args, **kwargs):
        if not self.count_number:
            last = CycleCount.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.count_number:
                try:
                    num = int(last.count_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.count_number = f"CC-{num:05d}"
        super().save(*args, **kwargs)


class CycleCountItem(models.Model):
    cycle_count = models.ForeignKey(
        CycleCount,
        on_delete=models.CASCADE,
        related_name='items',
    )
    bin = models.ForeignKey(
        Bin,
        on_delete=models.SET_NULL,
        related_name='cycle_count_items',
        blank=True,
        null=True,
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='cycle_count_items',
    )
    expected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    counted_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='counted_items',
        blank=True,
        null=True,
    )
    counted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} - Variance: {self.variance}"


# =============================================================================
# YARD MANAGEMENT
# =============================================================================

class YardLocation(models.Model):
    LOCATION_TYPE_CHOICES = [
        ('dock_door', 'Dock Door'),
        ('parking_spot', 'Parking Spot'),
        ('staging_area', 'Staging Area'),
        ('gate', 'Gate'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='yard_locations',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='yard_locations',
    )
    location_code = models.CharField(max_length=50)
    location_type = models.CharField(
        max_length=20, choices=LOCATION_TYPE_CHOICES, default='parking_spot',
    )
    is_occupied = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'location_code')
        ordering = ['warehouse', 'location_code']

    def __str__(self):
        return f"{self.location_code} ({self.get_location_type_display()})"

    def save(self, *args, **kwargs):
        if not self.location_code:
            last = YardLocation.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.location_code:
                try:
                    num = int(last.location_code.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.location_code = f"YL-{num:05d}"
        super().save(*args, **kwargs)


class YardVisit(models.Model):
    VISIT_TYPE_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
        ('drop_trailer', 'Drop Trailer'),
    ]

    STATUS_CHOICES = [
        ('expected', 'Expected'),
        ('checked_in', 'Checked In'),
        ('at_dock', 'At Dock'),
        ('loading', 'Loading'),
        ('unloading', 'Unloading'),
        ('completed', 'Completed'),
        ('departed', 'Departed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='yard_visits',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='yard_visits',
    )
    visit_number = models.CharField(max_length=50)
    yard_location = models.ForeignKey(
        YardLocation,
        on_delete=models.SET_NULL,
        related_name='visits',
        blank=True,
        null=True,
    )
    carrier_name = models.CharField(max_length=255)
    driver_name = models.CharField(max_length=255, blank=True)
    trailer_number = models.CharField(max_length=100, blank=True)
    truck_number = models.CharField(max_length=100, blank=True)
    visit_type = models.CharField(
        max_length=20, choices=VISIT_TYPE_CHOICES, default='inbound',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='expected')
    appointment = models.ForeignKey(
        DockAppointment,
        on_delete=models.SET_NULL,
        related_name='yard_visits',
        blank=True,
        null=True,
    )
    check_in_time = models.DateTimeField(blank=True, null=True)
    check_out_time = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'visit_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.visit_number} - {self.carrier_name}"

    def save(self, *args, **kwargs):
        if not self.visit_number:
            last = YardVisit.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.visit_number:
                try:
                    num = int(last.visit_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.visit_number = f"YV-{num:05d}"
        super().save(*args, **kwargs)
