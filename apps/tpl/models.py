from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# Central Entity: Client
# =============================================================================

class Client(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_clients',
    )
    client_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    default_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_clients', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '3PL Client'
        verbose_name_plural = '3PL Clients'
        unique_together = ('tenant', 'client_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.client_number:
            last = Client.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.client_number:
                try:
                    num = int(last.client_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.client_number = f"CLT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def days_until_contract_end(self):
        if self.contract_end_date:
            delta = self.contract_end_date - timezone.now().date()
            return delta.days
        return None


# =============================================================================
# 1. Client Billing
# =============================================================================

class BillingRate(models.Model):
    RATE_TYPE_CHOICES = [
        ('storage', 'Per Storage Unit'),
        ('transaction', 'Per Transaction'),
        ('weight', 'Per Weight Unit'),
        ('fixed', 'Fixed Fee'),
    ]

    CURRENCY_CHOICES = Client.CURRENCY_CHOICES

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_billing_rates',
    )
    rate_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='billing_rates',
    )
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='storage')
    description = models.CharField(max_length=255)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    rate_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    effective_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_billing_rates', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Billing Rate'
        verbose_name_plural = 'Billing Rates'
        unique_together = ('tenant', 'rate_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rate_number} - {self.description}"

    def save(self, *args, **kwargs):
        if not self.rate_number:
            last = BillingRate.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.rate_number:
                try:
                    num = int(last.rate_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.rate_number = f"BRT-{num:05d}"
        super().save(*args, **kwargs)


class BillingInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    CURRENCY_CHOICES = Client.CURRENCY_CHOICES

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_billing_invoices',
    )
    invoice_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='billing_invoices',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    due_date = models.DateField(blank=True, null=True)
    issued_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_billing_invoices', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Billing Invoice'
        verbose_name_plural = 'Billing Invoices'
        unique_together = ('tenant', 'invoice_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = BillingInvoice.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.invoice_number:
                try:
                    num = int(last.invoice_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.invoice_number = f"INV-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ('paid', 'cancelled'):
            return timezone.now().date() > self.due_date
        return False

    @property
    def line_item_count(self):
        return self.line_items.count()


class BillingInvoiceItem(models.Model):
    invoice = models.ForeignKey(
        BillingInvoice, on_delete=models.CASCADE, related_name='line_items',
    )
    description = models.CharField(max_length=255)
    rate = models.ForeignKey(
        BillingRate, on_delete=models.SET_NULL, blank=True, null=True,
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Invoice Line Item'
        verbose_name_plural = 'Invoice Line Items'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} (x{self.quantity})"


# =============================================================================
# 2. Client Inventory Segregation
# =============================================================================

class ClientStorageZone(models.Model):
    ZONE_TYPE_CHOICES = [
        ('dedicated', 'Dedicated'),
        ('shared', 'Shared'),
    ]

    CAPACITY_UNIT_CHOICES = [
        ('sqft', 'Sq Ft'),
        ('sqm', 'Sq M'),
        ('pallets', 'Pallet Positions'),
        ('cbm', 'Cubic Meters'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_storage_zones',
    )
    zone_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='storage_zones',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='tpl_storage_zones',
    )
    zone_name = models.CharField(max_length=255)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPE_CHOICES, default='dedicated')
    location_description = models.CharField(max_length=255, blank=True)
    capacity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    capacity_unit = models.CharField(max_length=10, choices=CAPACITY_UNIT_CHOICES, default='sqft')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_storage_zones', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client Storage Zone'
        verbose_name_plural = 'Client Storage Zones'
        unique_together = ('tenant', 'zone_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.zone_number} - {self.zone_name}"

    def save(self, *args, **kwargs):
        if not self.zone_number:
            last = ClientStorageZone.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.zone_number:
                try:
                    num = int(last.zone_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.zone_number = f"CSZ-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def inventory_count(self):
        return self.inventory_items.count()


class ClientInventoryItem(models.Model):
    WEIGHT_UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('lbs', 'Pounds'),
        ('mt', 'Metric Tons'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_inventory_items',
    )
    tracking_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='inventory_items',
    )
    storage_zone = models.ForeignKey(
        ClientStorageZone, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='inventory_items',
    )
    item_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_of_measure = models.CharField(max_length=50, default='units')
    weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    weight_unit = models.CharField(max_length=5, choices=WEIGHT_UNIT_CHOICES, default='kg')
    received_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_inventory_items', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client Inventory Item'
        verbose_name_plural = 'Client Inventory Items'
        unique_together = ('tenant', 'tracking_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} - {self.item_name}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            last = ClientInventoryItem.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.tracking_number:
                try:
                    num = int(last.tracking_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.tracking_number = f"CII-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# 3. SLA Management
# =============================================================================

class SLA(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('breached', 'Breached'),
        ('expired', 'Expired'),
    ]

    REVIEW_FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_slas',
    )
    sla_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='slas',
    )
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    effective_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    review_frequency = models.CharField(
        max_length=20, choices=REVIEW_FREQUENCY_CHOICES, default='monthly',
    )
    description = models.TextField(blank=True)
    penalty_clause = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_slas', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'SLA'
        verbose_name_plural = 'SLAs'
        unique_together = ('tenant', 'sla_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sla_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.sla_number:
            last = SLA.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.sla_number:
                try:
                    num = int(last.sla_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.sla_number = f"SLA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def days_until_expiry(self):
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None

    @property
    def metric_count(self):
        return self.metrics.count()

    @property
    def breached_metric_count(self):
        return self.metrics.filter(is_breached=True).count()


class SLAMetric(models.Model):
    METRIC_TYPE_CHOICES = [
        ('on_time_delivery', 'On-Time Delivery %'),
        ('order_accuracy', 'Order Accuracy %'),
        ('turnaround_time', 'Turnaround Time (hrs)'),
        ('damage_rate', 'Damage Rate %'),
        ('custom', 'Custom'),
    ]

    sla = models.ForeignKey(
        SLA, on_delete=models.CASCADE, related_name='metrics',
    )
    metric_name = models.CharField(max_length=255)
    metric_type = models.CharField(
        max_length=30, choices=METRIC_TYPE_CHOICES, default='custom',
    )
    target_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True)
    measurement_period = models.CharField(max_length=50, blank=True)
    is_breached = models.BooleanField(default=False)
    breach_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'SLA Metric'
        verbose_name_plural = 'SLA Metrics'
        ordering = ['id']

    def __str__(self):
        return f"{self.metric_name} (Target: {self.target_value})"


# =============================================================================
# 4. Client Integration
# =============================================================================

class IntegrationConfig(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
        ('disabled', 'Disabled'),
    ]

    SYNC_DIRECTION_CHOICES = [
        ('inbound', 'Inbound (From Client)'),
        ('outbound', 'Outbound (To Client)'),
        ('bidirectional', 'Bidirectional'),
    ]

    SYNC_FREQUENCY_CHOICES = [
        ('realtime', 'Real-Time'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('manual', 'Manual'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_integrations',
    )
    config_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='integrations',
    )
    integration_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    api_key = models.CharField(max_length=255, blank=True)
    api_endpoint = models.URLField(blank=True)
    webhook_url = models.URLField(blank=True)
    sync_direction = models.CharField(
        max_length=20, choices=SYNC_DIRECTION_CHOICES, default='bidirectional',
    )
    sync_frequency = models.CharField(
        max_length=20, choices=SYNC_FREQUENCY_CHOICES, default='daily',
    )
    last_sync_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_integrations', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Integration Config'
        verbose_name_plural = 'Integration Configs'
        unique_together = ('tenant', 'config_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.config_number} - {self.integration_name}"

    def save(self, *args, **kwargs):
        if not self.config_number:
            last = IntegrationConfig.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.config_number:
                try:
                    num = int(last.config_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.config_number = f"INT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def log_count(self):
        return self.logs.count()


class IntegrationLog(models.Model):
    LOG_TYPE_CHOICES = [
        ('sync', 'Sync'),
        ('webhook', 'Webhook'),
        ('error', 'Error'),
    ]

    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]

    integration = models.ForeignKey(
        IntegrationConfig, on_delete=models.CASCADE, related_name='logs',
    )
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES, default='sync')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='inbound')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    records_processed = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    request_payload = models.TextField(blank=True)
    response_payload = models.TextField(blank=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Integration Log'
        verbose_name_plural = 'Integration Logs'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.get_log_type_display()} - {self.get_status_display()} ({self.started_at})"


# =============================================================================
# 5. Warehouse Rental Management
# =============================================================================

class RentalAgreement(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    SPACE_TYPE_CHOICES = [
        ('dedicated', 'Dedicated Space'),
        ('shared', 'Shared Space'),
    ]

    AREA_UNIT_CHOICES = [
        ('sqft', 'Sq Ft'),
        ('sqm', 'Sq M'),
        ('pallets', 'Pallet Positions'),
    ]

    RATE_PERIOD_CHOICES = [
        ('daily', 'Per Day'),
        ('weekly', 'Per Week'),
        ('monthly', 'Per Month'),
    ]

    CURRENCY_CHOICES = Client.CURRENCY_CHOICES

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='tpl_rental_agreements',
    )
    agreement_number = models.CharField(max_length=50)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='rental_agreements',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    space_type = models.CharField(max_length=20, choices=SPACE_TYPE_CHOICES, default='dedicated')
    warehouse = models.ForeignKey(
        'inventory.Warehouse', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='tpl_rental_agreements',
    )
    area_size = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    area_unit = models.CharField(max_length=10, choices=AREA_UNIT_CHOICES, default='sqft')
    rate_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_period = models.CharField(max_length=10, choices=RATE_PERIOD_CHOICES, default='monthly')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    terms = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='created_tpl_rental_agreements', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rental Agreement'
        verbose_name_plural = 'Rental Agreements'
        unique_together = ('tenant', 'agreement_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agreement_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        if not self.agreement_number:
            last = RentalAgreement.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.agreement_number:
                try:
                    num = int(last.agreement_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.agreement_number = f"RNT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def days_until_expiry(self):
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return delta.days
        return None

    @property
    def usage_record_count(self):
        return self.usage_records.count()


class SpaceUsageRecord(models.Model):
    agreement = models.ForeignKey(
        RentalAgreement, on_delete=models.CASCADE, related_name='usage_records',
    )
    period_start = models.DateField()
    period_end = models.DateField()
    area_used = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    calculated_charge = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Space Usage Record'
        verbose_name_plural = 'Space Usage Records'
        ordering = ['-period_start']

    def __str__(self):
        return f"{self.period_start} to {self.period_end} ({self.utilization_percentage}%)"
