from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# PORTAL ACCOUNT
# =============================================================================

class PortalAccount(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery'),
        ('store_credit', 'Store Credit'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='portal_accounts',
    )
    account_number = models.CharField(max_length=50)
    customer = models.ForeignKey(
        'oms.Customer',
        on_delete=models.CASCADE,
        related_name='portal_accounts',
    )
    display_name = models.CharField(max_length=255)
    portal_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'), ('es', 'Spanish'), ('fr', 'French'),
            ('de', 'German'), ('ar', 'Arabic'), ('ur', 'Urdu'),
            ('zh', 'Chinese'),
        ],
        default='en',
    )
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer',
    )
    payment_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_portal_accounts',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Portal Account'
        verbose_name_plural = 'Portal Accounts'
        unique_together = ('tenant', 'account_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account_number} - {self.display_name}"

    def save(self, *args, **kwargs):
        if not self.account_number:
            last = PortalAccount.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.account_number:
                try:
                    num = int(last.account_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.account_number = f"PA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def ticket_count(self):
        return self.support_tickets.count()

    @property
    def document_count(self):
        return self.portal_documents.count()


# =============================================================================
# ORDER TRACKING
# =============================================================================

class OrderTracking(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('delayed', 'Delayed'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='order_trackings',
    )
    tracking_number = models.CharField(max_length=50)
    portal_account = models.ForeignKey(
        PortalAccount,
        on_delete=models.CASCADE,
        related_name='order_trackings',
    )
    order = models.ForeignKey(
        'oms.Order',
        on_delete=models.CASCADE,
        related_name='portal_trackings',
    )
    shipment = models.ForeignKey(
        'tms.Shipment',
        on_delete=models.SET_NULL,
        related_name='portal_trackings',
        blank=True,
        null=True,
    )
    current_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='processing',
    )
    estimated_delivery = models.DateField(blank=True, null=True)
    actual_delivery = models.DateField(blank=True, null=True)
    last_location = models.CharField(max_length=255, blank=True)
    carrier_name = models.CharField(max_length=255, blank=True)
    carrier_tracking_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_order_trackings',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order Tracking'
        verbose_name_plural = 'Order Trackings'
        unique_together = ('tenant', 'tracking_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} - {self.order}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            last = OrderTracking.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.tracking_number:
                try:
                    num = int(last.tracking_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.tracking_number = f"OT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_delivered(self):
        return self.current_status == 'delivered'

    @property
    def days_in_transit(self):
        if self.created_at:
            end = self.actual_delivery or timezone.now().date()
            return (end - self.created_at.date()).days
        return 0

    @property
    def event_count(self):
        return self.tracking_events.count()


class TrackingEvent(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('delayed', 'Delayed'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]

    tracking = models.ForeignKey(
        OrderTracking,
        on_delete=models.CASCADE,
        related_name='tracking_events',
    )
    event_date = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.get_status_display()} - {self.location}"


# =============================================================================
# PORTAL DOCUMENT
# =============================================================================

class PortalDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('proof_of_delivery', 'Proof of Delivery'),
        ('contract', 'Contract'),
        ('packing_list', 'Packing List'),
        ('credit_note', 'Credit Note'),
        ('statement', 'Statement'),
        ('certificate', 'Certificate'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='portal_documents',
    )
    document_number = models.CharField(max_length=50)
    portal_account = models.ForeignKey(
        PortalAccount,
        on_delete=models.CASCADE,
        related_name='portal_documents',
    )
    document_type = models.CharField(
        max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='invoice',
    )
    title = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, blank=True)
    order = models.ForeignKey(
        'oms.Order',
        on_delete=models.SET_NULL,
        related_name='portal_documents',
        blank=True,
        null=True,
    )
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='uploaded_portal_documents',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Portal Document'
        verbose_name_plural = 'Portal Documents'
        unique_together = ('tenant', 'document_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.document_number:
            last = PortalDocument.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.document_number:
                try:
                    num = int(last.document_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.document_number = f"DOC-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def file_size_display(self):
        if self.file_size > 1048576:
            return f"{self.file_size / 1048576:.1f} MB"
        elif self.file_size > 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size} B"


# =============================================================================
# SUPPORT TICKETING
# =============================================================================

class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('order_issue', 'Order Issue'),
        ('delivery_issue', 'Delivery Issue'),
        ('billing', 'Billing'),
        ('product_inquiry', 'Product Inquiry'),
        ('return_request', 'Return Request'),
        ('general', 'General'),
        ('complaint', 'Complaint'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_on_customer', 'Waiting on Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='support_tickets',
    )
    ticket_number = models.CharField(max_length=50)
    portal_account = models.ForeignKey(
        PortalAccount,
        on_delete=models.CASCADE,
        related_name='support_tickets',
    )
    order = models.ForeignKey(
        'oms.Order',
        on_delete=models.SET_NULL,
        related_name='support_tickets',
        blank=True,
        null=True,
    )
    subject = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default='general',
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium',
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_support_tickets',
        blank=True,
        null=True,
    )
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_support_tickets',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        unique_together = ('tenant', 'ticket_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last = SupportTicket.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.ticket_number:
                try:
                    num = int(last.ticket_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.ticket_number = f"TKT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_resolved(self):
        return self.status in ('resolved', 'closed')

    @property
    def response_time_hours(self):
        if self.resolved_at and self.created_at:
            return round((self.resolved_at - self.created_at).total_seconds() / 3600, 2)
        return 0

    @property
    def message_count(self):
        return self.messages.count()


class TicketMessage(models.Model):
    SENDER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender_name = models.CharField(max_length=255)
    sender_type = models.CharField(
        max_length=10, choices=SENDER_TYPE_CHOICES, default='customer',
    )
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender_name} ({self.get_sender_type_display()})"


# =============================================================================
# CATALOG BROWSING
# =============================================================================

class CatalogItem(models.Model):
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('pre_order', 'Pre-Order'),
        ('discontinued', 'Discontinued'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='catalog_items',
    )
    catalog_number = models.CharField(max_length=50)
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='portal_catalog_entries',
    )
    portal_name = models.CharField(max_length=255)
    portal_description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    stock_status = models.CharField(
        max_length=15, choices=STOCK_STATUS_CHOICES, default='in_stock',
    )
    available_quantity = models.PositiveIntegerField(default=0)
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    lead_time_days = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_catalog_items',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catalog Item'
        verbose_name_plural = 'Catalog Items'
        unique_together = ('tenant', 'catalog_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.catalog_number} - {self.portal_name}"

    def save(self, *args, **kwargs):
        if not self.catalog_number:
            last = CatalogItem.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.catalog_number:
                try:
                    num = int(last.catalog_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.catalog_number = f"CAT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.is_active and self.stock_status not in ('out_of_stock', 'discontinued')
