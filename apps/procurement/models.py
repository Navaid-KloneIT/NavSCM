import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# FOUNDATION MODELS
# =============================================================================

class ItemCategory(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='item_categories',
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Item Categories'
        unique_together = ('tenant', 'slug')
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    UOM_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('liter', 'Liter'),
        ('ml', 'Milliliter'),
        ('meter', 'Meter'),
        ('cm', 'Centimeter'),
        ('box', 'Box'),
        ('pack', 'Pack'),
        ('set', 'Set'),
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('unit', 'Unit'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='items',
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.SET_NULL,
        related_name='items',
        blank=True,
        null=True,
    )
    unit_of_measure = models.CharField(max_length=20, choices=UOM_CHOICES, default='piece')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Vendor(models.Model):
    PAYMENT_TERMS_CHOICES = [
        ('net_15', 'Net 15'),
        ('net_30', 'Net 30'),
        ('net_45', 'Net 45'),
        ('net_60', 'Net 60'),
        ('net_90', 'Net 90'),
        ('cod', 'Cash on Delivery'),
        ('advance', 'Advance Payment'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='vendors',
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(
        max_length=20, choices=PAYMENT_TERMS_CHOICES, default='net_30',
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_vendors',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# PURCHASE REQUISITION
# =============================================================================

class PurchaseRequisition(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
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
        related_name='purchase_requisitions',
    )
    requisition_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='purchase_requisitions',
        blank=True,
        null=True,
    )
    department = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    required_date = models.DateField(blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_requisitions',
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'requisition_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requisition_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            last = PurchaseRequisition.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.requisition_number:
                try:
                    num = int(last.requisition_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.requisition_number = f"PR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class PurchaseRequisitionItem(models.Model):
    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        related_name='requisition_items',
        blank=True,
        null=True,
    )
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    estimated_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    @property
    def total_price(self):
        return self.quantity * self.estimated_unit_price

    def __str__(self):
        return self.description or (self.item.name if self.item else f"Line {self.pk}")


# =============================================================================
# REQUEST FOR QUOTATION (RFQ)
# =============================================================================

class RFQ(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('evaluated', 'Evaluated'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='rfqs',
    )
    rfq_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.SET_NULL,
        related_name='rfqs',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_deadline = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_rfqs',
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'RFQ'
        verbose_name_plural = 'RFQs'
        unique_together = ('tenant', 'rfq_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rfq_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.rfq_number:
            last = RFQ.objects.filter(tenant=self.tenant).order_by('-created_at').first()
            if last and last.rfq_number:
                try:
                    num = int(last.rfq_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.rfq_number = f"RFQ-{num:05d}"
        super().save(*args, **kwargs)


class RFQItem(models.Model):
    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        related_name='rfq_items',
        blank=True,
        null=True,
    )
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_of_measure = models.CharField(max_length=20, choices=Item.UOM_CHOICES, default='piece')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.description or (self.item.name if self.item else f"Line {self.pk}")


class RFQVendor(models.Model):
    STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('quoted', 'Quoted'),
        ('declined', 'Declined'),
        ('no_response', 'No Response'),
    ]

    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.CASCADE,
        related_name='rfq_vendors',
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='rfq_invitations',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    invited_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('rfq', 'vendor')
        ordering = ['vendor__name']

    def __str__(self):
        return f"{self.vendor.name} - {self.rfq.rfq_number}"


class VendorQuote(models.Model):
    rfq_vendor = models.ForeignKey(
        RFQVendor,
        on_delete=models.CASCADE,
        related_name='quotes',
    )
    rfq_item = models.ForeignKey(
        RFQItem,
        on_delete=models.CASCADE,
        related_name='vendor_quotes',
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    lead_time_days = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    is_selected = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rfq_vendor', 'rfq_item')
        ordering = ['unit_price']

    def __str__(self):
        return f"{self.rfq_vendor.vendor.name} - {self.rfq_item}"


# =============================================================================
# PURCHASE ORDER
# =============================================================================

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('partially_received', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='purchase_orders',
    )
    po_number = models.CharField(max_length=50)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
    )
    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.SET_NULL,
        related_name='purchase_orders',
        blank=True,
        null=True,
    )
    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.SET_NULL,
        related_name='purchase_orders',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_terms = models.CharField(
        max_length=20, choices=Vendor.PAYMENT_TERMS_CHOICES, default='net_30',
    )
    shipping_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_purchase_orders',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_purchase_orders',
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'po_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.po_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            last = PurchaseOrder.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.po_number:
                try:
                    num = int(last.po_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.po_number = f"PO-{num:05d}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'total_amount'])


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        related_name='po_items',
        blank=True,
        null=True,
    )
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    @property
    def total_price(self):
        base = self.quantity * self.unit_price
        tax = base * (self.tax_rate / 100)
        return base + tax - self.discount

    def __str__(self):
        return self.description or (self.item.name if self.item else f"Line {self.pk}")


# =============================================================================
# VENDOR PORTAL
# =============================================================================

class VendorContact(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='vendor_contacts',
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='vendor_contacts',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"


class POAcknowledgement(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='acknowledgements',
    )
    acknowledged_by = models.ForeignKey(
        VendorContact,
        on_delete=models.SET_NULL,
        related_name='acknowledgements',
        blank=True,
        null=True,
    )
    acknowledged_at = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-acknowledged_at']

    def __str__(self):
        return f"Ack: {self.purchase_order.po_number}"


class ShipmentUpdate(models.Model):
    STATUS_CHOICES = [
        ('preparing', 'Preparing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='shipment_updates',
    )
    updated_by = models.ForeignKey(
        VendorContact,
        on_delete=models.SET_NULL,
        related_name='shipment_updates',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    estimated_arrival = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_status_display()} - {self.purchase_order.po_number}"


# =============================================================================
# INVOICE RECONCILIATION (3-WAY MATCHING)
# =============================================================================

class GoodsReceiptNote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partial'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='goods_receipt_notes',
    )
    grn_number = models.CharField(max_length=50)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='grns',
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='received_grns',
        blank=True,
        null=True,
    )
    received_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Goods Receipt Note'
        verbose_name_plural = 'Goods Receipt Notes'
        unique_together = ('tenant', 'grn_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.grn_number} - PO: {self.purchase_order.po_number}"

    def save(self, *args, **kwargs):
        if not self.grn_number:
            last = GoodsReceiptNote.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.grn_number:
                try:
                    num = int(last.grn_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.grn_number = f"GRN-{num:05d}"
        super().save(*args, **kwargs)


class GRNItem(models.Model):
    grn = models.ForeignKey(
        GoodsReceiptNote,
        on_delete=models.CASCADE,
        related_name='items',
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name='grn_items',
    )
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accepted_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"GRN Item: {self.po_item}"


class VendorInvoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('partially_matched', 'Partially Matched'),
        ('disputed', 'Disputed'),
        ('paid', 'Paid'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='vendor_invoices',
    )
    invoice_number = models.CharField(max_length=100)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='invoices',
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        related_name='vendor_invoices',
        blank=True,
        null=True,
    )
    grn = models.ForeignKey(
        GoodsReceiptNote,
        on_delete=models.SET_NULL,
        related_name='vendor_invoices',
        blank=True,
        null=True,
    )
    invoice_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'invoice_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.vendor.name}"


class VendorInvoiceItem(models.Model):
    invoice = models.ForeignKey(
        VendorInvoice,
        on_delete=models.CASCADE,
        related_name='items',
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.SET_NULL,
        related_name='invoice_items',
        blank=True,
        null=True,
    )
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.description or f"Invoice Item {self.pk}"


class ThreeWayMatch(models.Model):
    MATCH_STATUS_CHOICES = [
        ('full_match', 'Full Match'),
        ('partial_match', 'Partial Match'),
        ('mismatch', 'Mismatch'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='three_way_matches',
    )
    invoice = models.ForeignKey(
        VendorInvoice,
        on_delete=models.CASCADE,
        related_name='matches',
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='matches',
    )
    grn = models.ForeignKey(
        GoodsReceiptNote,
        on_delete=models.CASCADE,
        related_name='matches',
    )
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='mismatch')
    quantity_match = models.BooleanField(default=False)
    price_match = models.BooleanField(default=False)
    total_match = models.BooleanField(default=False)
    discrepancy_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='resolved_matches',
        blank=True,
        null=True,
    )
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Three-Way Match'
        verbose_name_plural = 'Three-Way Matches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Match: {self.invoice.invoice_number} / {self.purchase_order.po_number} / {self.grn.grn_number}"
