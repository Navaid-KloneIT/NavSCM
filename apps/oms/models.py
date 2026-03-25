from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================

class Customer(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='oms_customers',
    )
    customer_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=255, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'customer_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.customer_number:
            last = Customer.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.customer_number:
                try:
                    num = int(last.customer_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.customer_number = f"CUST-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# SALES CHANNEL
# =============================================================================

class SalesChannel(models.Model):
    CHANNEL_TYPE_CHOICES = [
        ('website', 'Website'),
        ('marketplace', 'Marketplace'),
        ('phone', 'Phone'),
        ('edi', 'EDI'),
        ('manual', 'Manual'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='oms_sales_channels',
    )
    name = models.CharField(max_length=255)
    channel_type = models.CharField(
        max_length=20, choices=CHANNEL_TYPE_CHOICES, default='manual',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_validation', 'Pending Validation'),
        ('validated', 'Validated'),
        ('allocated', 'Allocated'),
        ('in_fulfillment', 'In Fulfillment'),
        ('partially_shipped', 'Partially Shipped'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
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
        related_name='oms_orders',
    )
    order_number = models.CharField(max_length=50)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    sales_channel = models.ForeignKey(
        SalesChannel,
        on_delete=models.SET_NULL,
        related_name='orders',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    order_date = models.DateField()
    required_date = models.DateField(blank=True, null=True)
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='oms_orders_created',
        blank=True,
        null=True,
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='oms_orders_validated',
        blank=True,
        null=True,
    )
    validated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'order_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            last = Order.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.order_number:
                try:
                    num = int(last.order_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.order_number = f"ORD-{num:05d}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('allocated', 'Allocated'),
        ('partially_shipped', 'Partially Shipped'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='order_items',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    allocated_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        related_name='allocated_order_items',
        blank=True,
        null=True,
    )
    allocated_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipped_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


# =============================================================================
# ORDER VALIDATION
# =============================================================================

class OrderValidation(models.Model):
    VALIDATION_TYPE_CHOICES = [
        ('credit_check', 'Credit Check'),
        ('inventory_check', 'Inventory Check'),
        ('fraud_check', 'Fraud Check'),
        ('address_verification', 'Address Verification'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='oms_validations',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='validations',
    )
    validation_number = models.CharField(max_length=50)
    validation_type = models.CharField(
        max_length=30, choices=VALIDATION_TYPE_CHOICES,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_notes = models.TextField(blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='oms_validations',
        blank=True,
        null=True,
    )
    validated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'validation_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.validation_number} - {self.get_validation_type_display()}"

    def save(self, *args, **kwargs):
        if not self.validation_number:
            last = OrderValidation.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.validation_number:
                try:
                    num = int(last.validation_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.validation_number = f"OV-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# ORDER ALLOCATION
# =============================================================================

class OrderAllocation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('allocated', 'Allocated'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]

    ALLOCATION_METHOD_CHOICES = [
        ('nearest', 'Nearest Warehouse'),
        ('lowest_cost', 'Lowest Cost'),
        ('highest_stock', 'Highest Stock'),
        ('manual', 'Manual'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='oms_allocations',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='allocations',
    )
    allocation_number = models.CharField(max_length=50)
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='order_allocations',
    )
    allocation_method = models.CharField(
        max_length=20, choices=ALLOCATION_METHOD_CHOICES, default='manual',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    allocated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='oms_allocations',
        blank=True,
        null=True,
    )
    allocated_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'allocation_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.allocation_number} - {self.order.order_number}"

    def save(self, *args, **kwargs):
        if not self.allocation_number:
            last = OrderAllocation.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.allocation_number:
                try:
                    num = int(last.allocation_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.allocation_number = f"ALLOC-{num:05d}"
        super().save(*args, **kwargs)


class AllocationItem(models.Model):
    allocation = models.ForeignKey(
        OrderAllocation,
        on_delete=models.CASCADE,
        related_name='items',
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='allocation_items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='allocation_items',
    )
    requested_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allocated_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='allocation_items',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} - {self.allocated_quantity}/{self.requested_quantity}"


# =============================================================================
# BACKORDER MANAGEMENT
# =============================================================================

class Backorder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='oms_backorders',
    )
    backorder_number = models.CharField(max_length=50)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='backorders',
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='backorders',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='backorders',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fulfilled_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expected_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'backorder_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.backorder_number} - {self.item.name}"

    def save(self, *args, **kwargs):
        if not self.backorder_number:
            last = Backorder.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.backorder_number:
                try:
                    num = int(last.backorder_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.backorder_number = f"BO-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# CUSTOMER NOTIFICATIONS
# =============================================================================

class CustomerNotification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('order_confirmation', 'Order Confirmation'),
        ('order_validated', 'Order Validated'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('backorder_alert', 'Backorder Alert'),
        ('order_cancelled', 'Order Cancelled'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email & SMS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='oms_notifications',
    )
    notification_number = models.CharField(max_length=50)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPE_CHOICES,
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'notification_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_number} - {self.get_notification_type_display()}"

    def save(self, *args, **kwargs):
        if not self.notification_number:
            last = CustomerNotification.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.notification_number:
                try:
                    num = int(last.notification_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.notification_number = f"CN-{num:05d}"
        super().save(*args, **kwargs)
