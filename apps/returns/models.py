from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# RETURN MERCHANDISE AUTHORIZATION (RMA)
# =============================================================================

class ReturnAuthorization(models.Model):
    RETURN_TYPE_CHOICES = [
        ('exchange', 'Exchange'),
        ('refund', 'Refund'),
        ('repair', 'Repair'),
        ('store_credit', 'Store Credit'),
    ]

    REASON_CATEGORY_CHOICES = [
        ('defective', 'Defective'),
        ('wrong_item', 'Wrong Item'),
        ('damaged', 'Damaged'),
        ('not_as_described', 'Not As Described'),
        ('changed_mind', 'Changed Mind'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('receiving', 'Receiving'),
        ('received', 'Received'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
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
        related_name='return_authorizations',
    )
    rma_number = models.CharField(max_length=50)
    customer = models.ForeignKey(
        'oms.Customer',
        on_delete=models.CASCADE,
        related_name='return_authorizations',
    )
    order = models.ForeignKey(
        'oms.Order',
        on_delete=models.SET_NULL,
        related_name='return_authorizations',
        blank=True,
        null=True,
    )
    return_type = models.CharField(
        max_length=20, choices=RETURN_TYPE_CHOICES, default='refund',
    )
    reason_category = models.CharField(
        max_length=20, choices=REASON_CATEGORY_CHOICES, default='defective',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    requested_date = models.DateField(blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_rmas',
        blank=True,
        null=True,
    )
    approved_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_rmas',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Return Merchandise Authorization'
        verbose_name_plural = 'Return Merchandise Authorizations'
        unique_together = ('tenant', 'rma_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rma_number} - {self.customer}"

    def save(self, *args, **kwargs):
        if not self.rma_number:
            last = ReturnAuthorization.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.rma_number:
                try:
                    num = int(last.rma_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.rma_number = f"RMA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def days_since_request(self):
        if self.requested_date:
            return (timezone.now().date() - self.requested_date).days
        return 0

    @property
    def line_item_count(self):
        return self.line_items.count()

    @property
    def total_quantity(self):
        total = self.line_items.aggregate(total=models.Sum('quantity'))['total']
        return total or 0


class RMALineItem(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective'),
    ]

    rma = models.ForeignKey(
        ReturnAuthorization,
        on_delete=models.CASCADE,
        related_name='line_items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='rma_line_items',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    reason = models.TextField(blank=True)
    condition = models.CharField(
        max_length=15, choices=CONDITION_CHOICES, default='used',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


# =============================================================================
# REFUND PROCESSING
# =============================================================================

class Refund(models.Model):
    REFUND_TYPE_CHOICES = [
        ('full', 'Full'),
        ('partial', 'Partial'),
        ('store_credit', 'Store Credit'),
    ]

    REFUND_METHOD_CHOICES = [
        ('original_payment', 'Original Payment'),
        ('bank_transfer', 'Bank Transfer'),
        ('store_credit', 'Store Credit'),
        ('check', 'Check'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='refunds',
    )
    refund_number = models.CharField(max_length=50)
    rma = models.ForeignKey(
        ReturnAuthorization,
        on_delete=models.CASCADE,
        related_name='refunds',
    )
    refund_type = models.CharField(
        max_length=20, choices=REFUND_TYPE_CHOICES, default='full',
    )
    refund_method = models.CharField(
        max_length=20, choices=REFUND_METHOD_CHOICES, default='original_payment',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_refunds',
        blank=True,
        null=True,
    )
    processed_date = models.DateField(blank=True, null=True)
    transaction_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_refunds',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'refund_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.refund_number} - {self.rma.rma_number}"

    def save(self, *args, **kwargs):
        if not self.refund_number:
            last = Refund.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.refund_number:
                try:
                    num = int(last.refund_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.refund_number = f"REF-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# DISPOSITION MANAGEMENT
# =============================================================================

class Disposition(models.Model):
    CONDITION_RECEIVED_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective'),
    ]

    DISPOSITION_DECISION_CHOICES = [
        ('restock', 'Restock'),
        ('refurbish', 'Refurbish'),
        ('repair', 'Repair'),
        ('scrap', 'Scrap'),
        ('return_to_supplier', 'Return to Supplier'),
        ('donate', 'Donate'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('inspecting', 'Inspecting'),
        ('decided', 'Decided'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='dispositions',
    )
    disposition_number = models.CharField(max_length=50)
    rma = models.ForeignKey(
        ReturnAuthorization,
        on_delete=models.CASCADE,
        related_name='dispositions',
    )
    rma_item = models.ForeignKey(
        RMALineItem,
        on_delete=models.SET_NULL,
        related_name='dispositions',
        blank=True,
        null=True,
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='dispositions',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    condition_received = models.CharField(
        max_length=15, choices=CONDITION_RECEIVED_CHOICES, default='good',
    )
    disposition_decision = models.CharField(
        max_length=25, choices=DISPOSITION_DECISION_CHOICES, blank=True,
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_dispositions',
        blank=True,
        null=True,
    )
    inspection_notes = models.TextField(blank=True)
    decision_notes = models.TextField(blank=True)
    completed_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_dispositions',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'disposition_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.disposition_number} - {self.item.name}"

    def save(self, *args, **kwargs):
        if not self.disposition_number:
            last = Disposition.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.disposition_number:
                try:
                    num = int(last.disposition_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.disposition_number = f"DSP-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# WARRANTY CLAIMS
# =============================================================================

class WarrantyClaim(models.Model):
    CLAIM_TYPE_CHOICES = [
        ('manufacturer_warranty', 'Manufacturer Warranty'),
        ('supplier_warranty', 'Supplier Warranty'),
        ('extended_warranty', 'Extended Warranty'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('settled', 'Settled'),
        ('denied', 'Denied'),
        ('closed', 'Closed'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='warranty_claims',
    )
    claim_number = models.CharField(max_length=50)
    rma = models.ForeignKey(
        ReturnAuthorization,
        on_delete=models.SET_NULL,
        related_name='warranty_claims',
        blank=True,
        null=True,
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='warranty_claims',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='warranty_claims',
    )
    claim_type = models.CharField(
        max_length=25, choices=CLAIM_TYPE_CHOICES, default='manufacturer_warranty',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    warranty_start_date = models.DateField(blank=True, null=True)
    warranty_end_date = models.DateField(blank=True, null=True)
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    description = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_warranty_claims',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Warranty Claim'
        verbose_name_plural = 'Warranty Claims'
        unique_together = ('tenant', 'claim_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.claim_number} - {self.item.name}"

    def save(self, *args, **kwargs):
        if not self.claim_number:
            last = WarrantyClaim.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.claim_number:
                try:
                    num = int(last.claim_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.claim_number = f"WC-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_warranty_active(self):
        if self.warranty_end_date:
            return timezone.now().date() <= self.warranty_end_date
        return False

    @property
    def days_since_submitted(self):
        if self.created_at:
            return (timezone.now().date() - self.created_at.date()).days
        return 0


class WarrantyClaimItem(models.Model):
    claim = models.ForeignKey(
        WarrantyClaim,
        on_delete=models.CASCADE,
        related_name='claim_items',
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description} x {self.quantity}"


# =============================================================================
# RETURN PORTAL SETTINGS
# =============================================================================

class ReturnPortalSettings(models.Model):
    tenant = models.OneToOneField(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='return_portal_settings',
    )
    is_portal_enabled = models.BooleanField(default=False)
    return_window_days = models.PositiveIntegerField(default=30)
    requires_approval = models.BooleanField(default=True)
    auto_generate_labels = models.BooleanField(default=False)
    restocking_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
    )
    return_policy_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Return Portal Settings'
        verbose_name_plural = 'Return Portal Settings'

    def __str__(self):
        return f"Return Portal Settings - {self.tenant}"
