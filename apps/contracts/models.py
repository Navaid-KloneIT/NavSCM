from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# CONTRACT REPOSITORY
# =============================================================================

class Contract(models.Model):
    CONTRACT_TYPE_CHOICES = [
        ('logistics', 'Logistics Contract'),
        ('supplier_agreement', 'Supplier Agreement'),
        ('nda', 'Non-Disclosure Agreement'),
        ('service_agreement', 'Service Agreement'),
        ('lease', 'Lease Agreement'),
        ('purchase_agreement', 'Purchase Agreement'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='contracts',
    )
    contract_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    contract_type = models.CharField(
        max_length=25, choices=CONTRACT_TYPE_CHOICES, default='supplier_agreement',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.SET_NULL,
        related_name='compliance_contracts',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    description = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    auto_renew = models.BooleanField(default=False)
    renewal_period_days = models.PositiveIntegerField(default=0)
    notice_period_days = models.PositiveIntegerField(default=30)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_compliance_contracts',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'
        unique_together = ('tenant', 'contract_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.contract_number:
            last = Contract.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.contract_number:
                try:
                    num = int(last.contract_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.contract_number = f"CTR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if self.start_date and self.end_date:
            today = timezone.now().date()
            return self.start_date <= today <= self.end_date
        return False

    @property
    def days_until_expiry(self):
        if self.end_date:
            delta = (self.end_date - timezone.now().date()).days
            return max(delta, 0)
        return 0

    @property
    def document_count(self):
        return self.documents.count()


class ContractDocument(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    document_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_reference = models.CharField(max_length=500, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.document_name


# =============================================================================
# COMPLIANCE TRACKING
# =============================================================================

class ComplianceRecord(models.Model):
    REGULATION_TYPE_CHOICES = [
        ('fda', 'FDA'),
        ('hazmat', 'HazMat'),
        ('gdpr', 'GDPR'),
        ('iso', 'ISO'),
        ('customs', 'Customs'),
        ('environmental', 'Environmental'),
        ('labor', 'Labor'),
        ('trade_sanctions', 'Trade Sanctions'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_compliance', 'In Compliance'),
        ('non_compliant', 'Non-Compliant'),
        ('under_review', 'Under Review'),
        ('expired', 'Expired'),
    ]

    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='compliance_records',
    )
    compliance_number = models.CharField(max_length=50)
    regulation_name = models.CharField(max_length=255)
    regulation_type = models.CharField(
        max_length=20, choices=REGULATION_TYPE_CHOICES, default='other',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    compliance_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='compliance_responsibilities',
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    risk_level = models.CharField(
        max_length=10, choices=RISK_LEVEL_CHOICES, default='low',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_compliance_records',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compliance Record'
        verbose_name_plural = 'Compliance Records'
        unique_together = ('tenant', 'compliance_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.compliance_number} - {self.regulation_name}"

    def save(self, *args, **kwargs):
        if not self.compliance_number:
            last = ComplianceRecord.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.compliance_number:
                try:
                    num = int(last.compliance_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.compliance_number = f"CMP-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def days_until_expiry(self):
        if self.expiry_date:
            delta = (self.expiry_date - timezone.now().date()).days
            return max(delta, 0)
        return 0

    @property
    def check_item_count(self):
        return self.check_items.count()


class ComplianceCheckItem(models.Model):
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
        ('pending', 'Pending'),
    ]

    compliance_record = models.ForeignKey(
        ComplianceRecord,
        on_delete=models.CASCADE,
        related_name='check_items',
    )
    check_item = models.CharField(max_length=255)
    result = models.CharField(
        max_length=10, choices=RESULT_CHOICES, default='pending',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.check_item} - {self.get_result_display()}"


# =============================================================================
# TRADE DOCUMENTATION
# =============================================================================

class TradeDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('bill_of_lading', 'Bill of Lading'),
        ('commercial_invoice', 'Commercial Invoice'),
        ('packing_list', 'Packing List'),
        ('certificate_of_origin', 'Certificate of Origin'),
        ('customs_declaration', 'Customs Declaration'),
        ('letter_of_credit', 'Letter of Credit'),
        ('insurance_certificate', 'Insurance Certificate'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('archived', 'Archived'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='trade_documents',
    )
    document_number = models.CharField(max_length=50)
    document_type = models.CharField(
        max_length=25, choices=DOCUMENT_TYPE_CHOICES, default='bill_of_lading',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.SET_NULL,
        related_name='trade_documents',
        blank=True,
        null=True,
    )
    origin_country = models.CharField(max_length=100, blank=True)
    destination_country = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True)
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_trade_documents',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Trade Document'
        verbose_name_plural = 'Trade Documents'
        unique_together = ('tenant', 'document_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document_number} - {self.get_document_type_display()}"

    def save(self, *args, **kwargs):
        if not self.document_number:
            last = TradeDocument.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.document_number:
                try:
                    num = int(last.document_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.document_number = f"TD-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def line_item_count(self):
        return self.line_items.count()

    @property
    def total_value(self):
        total = self.line_items.aggregate(
            total=models.Sum('total_value')
        )['total']
        return total or self.value


class TradeDocumentItem(models.Model):
    trade_document = models.ForeignKey(
        TradeDocument,
        on_delete=models.CASCADE,
        related_name='line_items',
    )
    item_description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item_description} x {self.quantity}"


# =============================================================================
# LICENSE MANAGEMENT
# =============================================================================

class License(models.Model):
    LICENSE_TYPE_CHOICES = [
        ('import', 'Import License'),
        ('export', 'Export License'),
        ('transit', 'Transit Permit'),
        ('special_permit', 'Special Permit'),
        ('bonded_warehouse', 'Bonded Warehouse License'),
        ('customs_broker', 'Customs Broker License'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='licenses',
    )
    license_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    license_type = models.CharField(
        max_length=20, choices=LICENSE_TYPE_CHOICES, default='import',
    )
    issuing_authority = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    license_reference = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    renewal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_licenses',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'License'
        verbose_name_plural = 'Licenses'
        unique_together = ('tenant', 'license_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.license_number:
            last = License.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.license_number:
                try:
                    num = int(last.license_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.license_number = f"LIC-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def days_until_expiry(self):
        if self.expiry_date:
            delta = (self.expiry_date - timezone.now().date()).days
            return max(delta, 0)
        return 0

    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            delta = (self.expiry_date - timezone.now().date()).days
            return 0 < delta <= 30
        return False


# =============================================================================
# SUSTAINABILITY TRACKING
# =============================================================================

class SustainabilityReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('carbon_footprint', 'Carbon Footprint'),
        ('ethical_sourcing', 'Ethical Sourcing'),
        ('waste_management', 'Waste Management'),
        ('energy_consumption', 'Energy Consumption'),
        ('water_usage', 'Water Usage'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('published', 'Published'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='sustainability_reports',
    )
    report_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    report_type = models.CharField(
        max_length=20, choices=REPORT_TYPE_CHOICES, default='carbon_footprint',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(blank=True, null=True)
    total_carbon_footprint = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Total CO2 emissions in metric tons',
    )
    carbon_offset = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Carbon offset in metric tons',
    )
    sustainability_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Score from 0 to 100',
    )
    description = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_sustainability_reports',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sustainability Report'
        verbose_name_plural = 'Sustainability Reports'
        unique_together = ('tenant', 'report_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            last = SustainabilityReport.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.report_number:
                try:
                    num = int(last.report_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.report_number = f"SUS-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def net_carbon(self):
        return self.total_carbon_footprint - self.carbon_offset

    @property
    def metric_count(self):
        return self.metrics.count()


class SustainabilityMetric(models.Model):
    report = models.ForeignKey(
        SustainabilityReport,
        on_delete=models.CASCADE,
        related_name='metrics',
    )
    metric_name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, blank=True)
    target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"
