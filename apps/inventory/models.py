from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# FOUNDATION MODELS
# =============================================================================

class Warehouse(models.Model):
    WAREHOUSE_TYPE_CHOICES = [
        ('main', 'Main Warehouse'),
        ('branch', 'Branch Warehouse'),
        ('transit', 'Transit Warehouse'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='warehouses',
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    warehouse_type = models.CharField(
        max_length=20, choices=WAREHOUSE_TYPE_CHOICES, default='main',
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            last = Warehouse.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.code:
                try:
                    num = int(last.code.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.code = f"WH-{num:05d}"
        super().save(*args, **kwargs)


class WarehouseLocation(models.Model):
    ZONE_CHOICES = [
        ('receiving', 'Receiving'),
        ('storage', 'Storage'),
        ('picking', 'Picking'),
        ('shipping', 'Shipping'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='warehouse_locations',
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='locations',
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    zone = models.CharField(max_length=20, choices=ZONE_CHOICES, default='storage')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'warehouse', 'code')
        ordering = ['warehouse', 'zone', 'name']

    def __str__(self):
        return f"{self.warehouse.code}/{self.code} - {self.name}"


# =============================================================================
# STOCK CONTROL
# =============================================================================

class StockItem(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='stock_items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='stock_items',
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_items',
    )
    location = models.ForeignKey(
        WarehouseLocation,
        on_delete=models.SET_NULL,
        related_name='stock_items',
        blank=True,
        null=True,
    )
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    batch_number = models.CharField(max_length=100, blank=True, default='')
    serial_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_received_date = models.DateTimeField(blank=True, null=True)
    last_issued_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'item', 'warehouse', 'batch_number')
        ordering = ['item__name', 'warehouse__name']

    def __str__(self):
        return f"{self.item.name} @ {self.warehouse.name}"

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    @property
    def is_below_reorder(self):
        return self.quantity_on_hand <= self.reorder_point and self.reorder_point > 0

    @property
    def is_below_safety(self):
        return self.quantity_on_hand <= self.safety_stock and self.safety_stock > 0


# =============================================================================
# WAREHOUSE TRANSFER
# =============================================================================

class WarehouseTransfer(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='warehouse_transfers',
    )
    transfer_number = models.CharField(max_length=50)
    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='outgoing_transfers',
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='incoming_transfers',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='requested_transfers',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_transfers',
        blank=True,
        null=True,
    )
    transfer_date = models.DateField(blank=True, null=True)
    received_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'transfer_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transfer_number}"

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            last = WarehouseTransfer.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.transfer_number:
                try:
                    num = int(last.transfer_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.transfer_number = f"TRF-{num:05d}"
        super().save(*args, **kwargs)


class WarehouseTransferItem(models.Model):
    transfer = models.ForeignKey(
        WarehouseTransfer,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='transfer_items',
    )
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_sent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} x {self.quantity_requested}"


# =============================================================================
# STOCK ADJUSTMENT
# =============================================================================

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPE_CHOICES = [
        ('write_off', 'Write Off'),
        ('damage', 'Damage'),
        ('cycle_count', 'Cycle Count'),
        ('correction', 'Correction'),
        ('return', 'Return'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='stock_adjustments',
    )
    adjustment_number = models.CharField(max_length=50)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='adjustments',
    )
    adjustment_type = models.CharField(
        max_length=20, choices=ADJUSTMENT_TYPE_CHOICES, default='correction',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    reason = models.TextField(blank=True)
    adjusted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='adjusted_stock',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_adjustments',
        blank=True,
        null=True,
    )
    adjustment_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'adjustment_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.adjustment_number}"

    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            last = StockAdjustment.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.adjustment_number:
                try:
                    num = int(last.adjustment_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.adjustment_number = f"ADJ-{num:05d}"
        super().save(*args, **kwargs)


class StockAdjustmentItem(models.Model):
    adjustment = models.ForeignKey(
        StockAdjustment,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='adjustment_items',
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        related_name='adjustments',
        blank=True,
        null=True,
    )
    quantity_before = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_adjustment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} ({self.quantity_adjustment:+})"


# =============================================================================
# REORDER POINT AUTOMATION
# =============================================================================

class ReorderRule(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='reorder_rules',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='reorder_rules',
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='reorder_rules',
    )
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'item', 'warehouse')
        ordering = ['item__name']

    def __str__(self):
        return f"Reorder: {self.item.name} @ {self.warehouse.name}"


class ReorderSuggestion(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('dismissed', 'Dismissed'),
        ('po_created', 'PO Created'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='reorder_suggestions',
    )
    rule = models.ForeignKey(
        ReorderRule,
        on_delete=models.CASCADE,
        related_name='suggestions',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='reorder_suggestions',
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='reorder_suggestions',
    )
    suggested_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reorder: {self.item.name} x {self.suggested_quantity}"


# =============================================================================
# INVENTORY VALUATION
# =============================================================================

class InventoryValuation(models.Model):
    VALUATION_METHOD_CHOICES = [
        ('fifo', 'FIFO (First In, First Out)'),
        ('lifo', 'LIFO (Last In, First Out)'),
        ('weighted_avg', 'Weighted Average'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='inventory_valuations',
    )
    valuation_number = models.CharField(max_length=50)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        related_name='valuations',
        blank=True,
        null=True,
        help_text='Leave blank for all warehouses.',
    )
    valuation_method = models.CharField(
        max_length=20, choices=VALUATION_METHOD_CHOICES, default='weighted_avg',
    )
    valuation_date = models.DateField()
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_items = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_valuations',
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'valuation_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.valuation_number}"

    def save(self, *args, **kwargs):
        if not self.valuation_number:
            last = InventoryValuation.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.valuation_number:
                try:
                    num = int(last.valuation_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.valuation_number = f"VAL-{num:05d}"
        super().save(*args, **kwargs)


class InventoryValuationItem(models.Model):
    valuation = models.ForeignKey(
        InventoryValuation,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='valuation_items',
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='valuation_items',
    )
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valuation_method = models.CharField(max_length=20, default='weighted_avg')

    class Meta:
        ordering = ['item__name']

    def __str__(self):
        return f"{self.item.name} - {self.total_value}"
