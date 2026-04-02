from django.conf import settings
from django.db import models
from django.utils import timezone


CURRENCY_CHOICES = [
    ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
    ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
]

PAYMENT_METHOD_CHOICES = [
    ('bank_transfer', 'Bank Transfer'),
    ('check', 'Check'),
    ('cash', 'Cash'),
    ('wire', 'Wire Transfer'),
    ('credit_card', 'Credit Card'),
    ('other', 'Other'),
]


# =============================================================================
# 1. Accounts Payable
# =============================================================================

class APInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_TERMS_CHOICES = [
        ('due_on_receipt', 'Due on Receipt'),
        ('net_15', 'Net 15'),
        ('net_30', 'Net 30'),
        ('net_45', 'Net 45'),
        ('net_60', 'Net 60'),
        ('net_90', 'Net 90'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_ap_invoices',
    )
    invoice_number = models.CharField(max_length=50)
    vendor = models.ForeignKey(
        'procurement.Vendor', on_delete=models.CASCADE, related_name='ap_invoices',
    )
    purchase_order = models.ForeignKey(
        'procurement.PurchaseOrder', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='ap_invoices',
    )
    invoice_date = models.DateField()
    due_date = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='net_30')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_ap_invoices_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AP Invoice'
        verbose_name_plural = 'AP Invoices'
        unique_together = ('tenant', 'invoice_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = APInvoice.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.invoice_number:
                try:
                    num = int(last.invoice_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.invoice_number = f"AP-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def days_outstanding(self):
        return (timezone.now().date() - self.invoice_date).days

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ('paid', 'cancelled'):
            return timezone.now().date() > self.due_date
        return False

    @property
    def item_count(self):
        return self.items.count()


class APInvoiceItem(models.Model):
    invoice = models.ForeignKey(
        APInvoice, on_delete=models.CASCADE, related_name='items',
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'AP Invoice Item'
        verbose_name_plural = 'AP Invoice Items'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} (x{self.quantity})"


class APPayment(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_ap_payments',
    )
    payment_number = models.CharField(max_length=50)
    invoice = models.ForeignKey(
        APInvoice, on_delete=models.CASCADE, related_name='payments',
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_ap_payments_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AP Payment'
        verbose_name_plural = 'AP Payments'
        unique_together = ('tenant', 'payment_number')
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.payment_number} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            last = APPayment.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.payment_number:
                try:
                    num = int(last.payment_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.payment_number = f"APMT-{num:05d}"
        super().save(*args, **kwargs)
        self._update_invoice_status()

    def _update_invoice_status(self):
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        invoice.amount_paid = total_paid
        if total_paid >= invoice.total_amount:
            invoice.status = 'paid'
        elif total_paid > 0:
            invoice.status = 'partially_paid'
        invoice.save()


# =============================================================================
# 2. Accounts Receivable
# =============================================================================

class ARInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_ar_invoices',
    )
    invoice_number = models.CharField(max_length=50)
    customer = models.ForeignKey(
        'oms.Customer', on_delete=models.CASCADE, related_name='ar_invoices',
    )
    order = models.ForeignKey(
        'oms.Order', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='ar_invoices',
    )
    invoice_date = models.DateField()
    due_date = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_received = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_ar_invoices_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AR Invoice'
        verbose_name_plural = 'AR Invoices'
        unique_together = ('tenant', 'invoice_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = ARInvoice.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.invoice_number:
                try:
                    num = int(last.invoice_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.invoice_number = f"AR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_received

    @property
    def days_outstanding(self):
        return (timezone.now().date() - self.invoice_date).days

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ('paid', 'cancelled'):
            return timezone.now().date() > self.due_date
        return False

    @property
    def item_count(self):
        return self.items.count()


class ARInvoiceItem(models.Model):
    invoice = models.ForeignKey(
        ARInvoice, on_delete=models.CASCADE, related_name='items',
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'AR Invoice Item'
        verbose_name_plural = 'AR Invoice Items'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} (x{self.quantity})"


class ARPayment(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_ar_payments',
    )
    payment_number = models.CharField(max_length=50)
    invoice = models.ForeignKey(
        ARInvoice, on_delete=models.CASCADE, related_name='payments',
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_ar_payments_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AR Payment'
        verbose_name_plural = 'AR Payments'
        unique_together = ('tenant', 'payment_number')
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.payment_number} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            last = ARPayment.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.payment_number:
                try:
                    num = int(last.payment_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.payment_number = f"ARMT-{num:05d}"
        super().save(*args, **kwargs)
        self._update_invoice_status()

    def _update_invoice_status(self):
        invoice = self.invoice
        total_received = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        invoice.amount_received = total_received
        if total_received >= invoice.total_amount:
            invoice.status = 'paid'
        elif total_received > 0:
            invoice.status = 'partially_paid'
        invoice.save()


# =============================================================================
# 3. Landed Cost Calculation
# =============================================================================

class LandedCostSheet(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('finalized', 'Finalized'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_landed_costs',
    )
    sheet_number = models.CharField(max_length=50)
    shipment = models.ForeignKey(
        'tms.Shipment', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='landed_cost_sheets',
    )
    purchase_order = models.ForeignKey(
        'procurement.PurchaseOrder', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='landed_cost_sheets',
    )
    carrier = models.ForeignKey(
        'tms.Carrier', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='landed_cost_sheets',
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    total_goods_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_landed_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_landed_costs_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Landed Cost Sheet'
        verbose_name_plural = 'Landed Cost Sheets'
        unique_together = ('tenant', 'sheet_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sheet_number}"

    def save(self, *args, **kwargs):
        if not self.sheet_number:
            last = LandedCostSheet.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.sheet_number:
                try:
                    num = int(last.sheet_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.sheet_number = f"LC-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def component_count(self):
        return self.components.count()

    @property
    def total_additional_costs(self):
        return self.components.aggregate(total=models.Sum('amount'))['total'] or 0


class LandedCostComponent(models.Model):
    COST_TYPE_CHOICES = [
        ('freight', 'Freight'),
        ('customs_duty', 'Customs Duty'),
        ('insurance', 'Insurance'),
        ('handling', 'Handling'),
        ('inspection', 'Inspection'),
        ('warehousing', 'Warehousing'),
        ('brokerage', 'Brokerage'),
        ('other', 'Other'),
    ]

    ALLOCATION_CHOICES = [
        ('by_value', 'By Value'),
        ('by_weight', 'By Weight'),
        ('by_quantity', 'By Quantity'),
        ('equal', 'Equal'),
    ]

    sheet = models.ForeignKey(
        LandedCostSheet, on_delete=models.CASCADE, related_name='components',
    )
    cost_type = models.CharField(max_length=30, choices=COST_TYPE_CHOICES, default='freight')
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    allocation_method = models.CharField(max_length=20, choices=ALLOCATION_CHOICES, default='by_value')

    class Meta:
        verbose_name = 'Landed Cost Component'
        verbose_name_plural = 'Landed Cost Components'
        ordering = ['id']

    def __str__(self):
        return f"{self.get_cost_type_display()} - {self.amount}"


# =============================================================================
# 4. Budgeting
# =============================================================================

class Budget(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_budgets',
    )
    budget_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES, default='monthly')
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    planned_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_budgets_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
        unique_together = ('tenant', 'budget_number')
        ordering = ['-period_start']

    def __str__(self):
        return f"{self.budget_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.budget_number:
            last = Budget.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.budget_number:
                try:
                    num = int(last.budget_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.budget_number = f"BUD-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def variance(self):
        return self.planned_amount - self.actual_amount

    @property
    def variance_percentage(self):
        if self.planned_amount:
            return ((self.variance / self.planned_amount) * 100)
        return 0

    @property
    def is_over_budget(self):
        return self.actual_amount > self.planned_amount

    @property
    def entry_count(self):
        return self.entries.count()


class BudgetEntry(models.Model):
    budget = models.ForeignKey(
        Budget, on_delete=models.CASCADE, related_name='entries',
    )
    entry_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_budget_entries_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Budget Entry'
        verbose_name_plural = 'Budget Entries'
        ordering = ['-entry_date']

    def __str__(self):
        return f"{self.description} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_budget_actual()

    def delete(self, *args, **kwargs):
        budget = self.budget
        super().delete(*args, **kwargs)
        total = budget.entries.aggregate(total=models.Sum('amount'))['total'] or 0
        budget.actual_amount = total
        budget.save()

    def _update_budget_actual(self):
        budget = self.budget
        total = budget.entries.aggregate(total=models.Sum('amount'))['total'] or 0
        budget.actual_amount = total
        budget.save()


# =============================================================================
# 5. Tax Management
# =============================================================================

class TaxRate(models.Model):
    TAX_TYPE_CHOICES = [
        ('sales_tax', 'Sales Tax'),
        ('vat', 'VAT'),
        ('customs_duty', 'Customs Duty'),
        ('excise', 'Excise Tax'),
        ('withholding', 'Withholding Tax'),
        ('other', 'Other'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_tax_rates',
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    tax_type = models.CharField(max_length=30, choices=TAX_TYPE_CHOICES, default='sales_tax')
    rate = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(blank=True, null=True)
    effective_to = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tax Rate'
        verbose_name_plural = 'Tax Rates'
        unique_together = ('tenant', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    def save(self, *args, **kwargs):
        if not self.code:
            last = TaxRate.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.code:
                try:
                    num = int(last.code.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.code = f"TAX-{num:05d}"
        super().save(*args, **kwargs)


class TaxTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('collected', 'Collected'),
        ('paid', 'Paid'),
        ('refund', 'Refund'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.CASCADE, related_name='finance_tax_transactions',
    )
    transaction_number = models.CharField(max_length=50)
    tax_rate = models.ForeignKey(
        TaxRate, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='transactions',
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='collected')
    taxable_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    transaction_date = models.DateField()
    reference_type = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='finance_tax_transactions_created', blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tax Transaction'
        verbose_name_plural = 'Tax Transactions'
        unique_together = ('tenant', 'transaction_number')
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()}"

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            last = TaxTransaction.objects.filter(tenant=self.tenant).order_by('-id').first()
            if last and last.transaction_number:
                try:
                    num = int(last.transaction_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.transaction_number = f"TXLOG-{num:05d}"
        super().save(*args, **kwargs)
