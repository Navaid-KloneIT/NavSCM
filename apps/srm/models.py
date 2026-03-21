from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.procurement.models import Item


# =============================================================================
# SUPPLIER ONBOARDING
# =============================================================================

class SupplierOnboarding(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='supplier_onboardings',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='onboardings',
    )
    onboarding_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='submitted_onboardings',
        blank=True,
        null=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_onboardings',
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'onboarding_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.onboarding_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        if not self.onboarding_number:
            last = SupplierOnboarding.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.onboarding_number:
                try:
                    num = int(last.onboarding_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.onboarding_number = f"ONB-{num:05d}"
        super().save(*args, **kwargs)


class QualificationQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('financial', 'Financial'),
        ('quality', 'Quality'),
        ('compliance', 'Compliance'),
        ('safety', 'Safety'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='qualification_questions',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    question_text = models.TextField()
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.question_text[:50]}"


class QualificationResponse(models.Model):
    onboarding = models.ForeignKey(
        SupplierOnboarding,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    question = models.ForeignKey(
        QualificationQuestion,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    response_text = models.TextField(blank=True)
    attachments_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('onboarding', 'question')
        ordering = ['question__order']

    def __str__(self):
        return f"Response: {self.question.question_text[:30]}"


class DueDiligenceCheck(models.Model):
    CHECK_TYPE_CHOICES = [
        ('financial_verification', 'Financial Verification'),
        ('legal_compliance', 'Legal Compliance'),
        ('quality_certification', 'Quality Certification'),
        ('insurance_verification', 'Insurance Verification'),
        ('reference_check', 'Reference Check'),
        ('site_inspection', 'Site Inspection'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('waived', 'Waived'),
    ]

    onboarding = models.ForeignKey(
        SupplierOnboarding,
        on_delete=models.CASCADE,
        related_name='due_diligence_checks',
    )
    check_type = models.CharField(max_length=30, choices=CHECK_TYPE_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='due_diligence_checks',
        blank=True,
        null=True,
    )
    checked_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    attachments_note = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.get_check_type_display()} - {self.get_status_display()}"


# =============================================================================
# SUPPLIER SCORECARD
# =============================================================================

class ScorecardPeriod(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='scorecard_periods',
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'name')
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class SupplierScorecard(models.Model):
    RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
        ('poor', 'Poor'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='supplier_scorecards',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='scorecards',
    )
    period = models.ForeignKey(
        ScorecardPeriod,
        on_delete=models.CASCADE,
        related_name='scorecards',
    )
    scorecard_number = models.CharField(max_length=50)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rating = models.CharField(max_length=20, choices=RATING_CHOICES, default='satisfactory')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    delivery_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    responsiveness_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='evaluated_scorecards',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_scorecards',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'scorecard_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.scorecard_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        if not self.scorecard_number:
            last = SupplierScorecard.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.scorecard_number:
                try:
                    num = int(last.scorecard_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.scorecard_number = f"SC-{num:05d}"
        # Calculate overall score as average of the 4 dimension scores
        scores = [self.delivery_score, self.quality_score,
                  self.price_score, self.responsiveness_score]
        non_zero = [s for s in scores if s > 0]
        if non_zero:
            self.overall_score = sum(non_zero) / len(non_zero)
        super().save(*args, **kwargs)


class ScorecardCriteria(models.Model):
    CATEGORY_CHOICES = [
        ('delivery', 'Delivery'),
        ('quality', 'Quality'),
        ('price', 'Price'),
        ('responsiveness', 'Responsiveness'),
    ]

    scorecard = models.ForeignKey(
        SupplierScorecard,
        on_delete=models.CASCADE,
        related_name='criteria',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    criteria_name = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Scorecard Criteria'
        ordering = ['category', 'id']

    def __str__(self):
        return f"{self.criteria_name} ({self.get_category_display()})"


# =============================================================================
# CONTRACT MANAGEMENT
# =============================================================================

class SupplierContract(models.Model):
    TYPE_CHOICES = [
        ('master_agreement', 'Master Agreement'),
        ('purchase_agreement', 'Purchase Agreement'),
        ('service_agreement', 'Service Agreement'),
        ('nda', 'Non-Disclosure Agreement'),
        ('sla', 'Service Level Agreement'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('PKR', 'Pakistani Rupee'),
        ('AED', 'UAE Dirham'),
        ('SAR', 'Saudi Riyal'),
        ('INR', 'Indian Rupee'),
        ('CNY', 'Chinese Yuan'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='supplier_contracts',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='contracts',
    )
    contract_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    contract_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='purchase_agreement')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    payment_terms = models.CharField(
        max_length=20,
        choices=[
            ('net_15', 'Net 15'),
            ('net_30', 'Net 30'),
            ('net_45', 'Net 45'),
            ('net_60', 'Net 60'),
            ('net_90', 'Net 90'),
            ('cod', 'Cash on Delivery'),
            ('advance', 'Advance Payment'),
        ],
        default='net_30',
    )
    auto_renew = models.BooleanField(default=False)
    renewal_notice_days = models.PositiveIntegerField(default=30)
    terms_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_contracts',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_contracts',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'contract_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.contract_number:
            last = SupplierContract.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.contract_number:
                try:
                    num = int(last.contract_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.contract_number = f"CON-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_expiring_soon(self):
        if not self.end_date:
            return False
        days_left = (self.end_date - timezone.now().date()).days
        return 0 < days_left <= self.renewal_notice_days

    @property
    def days_until_expiry(self):
        if not self.end_date:
            return None
        return (self.end_date - timezone.now().date()).days


class ContractMilestone(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        related_name='milestones',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class ContractDocument(models.Model):
    TYPE_CHOICES = [
        ('contract', 'Contract'),
        ('amendment', 'Amendment'),
        ('addendum', 'Addendum'),
        ('attachment', 'Attachment'),
        ('correspondence', 'Correspondence'),
    ]

    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='contract')
    file = models.FileField(upload_to='contracts/%Y/%m/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='uploaded_contract_docs',
        blank=True,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"


# =============================================================================
# SUPPLIER CATALOG MANAGEMENT
# =============================================================================

class SupplierCatalog(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='supplier_catalogs',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='catalogs',
    )
    catalog_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    effective_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_catalogs',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'catalog_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.catalog_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.catalog_number:
            last = SupplierCatalog.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.catalog_number:
                try:
                    num = int(last.catalog_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.catalog_number = f"CAT-{num:05d}"
        super().save(*args, **kwargs)


class CatalogItem(models.Model):
    catalog = models.ForeignKey(
        SupplierCatalog,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='catalog_entries',
        blank=True,
        null=True,
    )
    supplier_part_number = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255, blank=True)
    unit_of_measure = models.CharField(
        max_length=20,
        choices=Item.UOM_CHOICES,
        default='piece',
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_order_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    lead_time_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.description or self.supplier_part_number or f"Catalog Item {self.pk}"


# =============================================================================
# RISK MANAGEMENT
# =============================================================================

class SupplierRiskAssessment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
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
        related_name='supplier_risk_assessments',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='risk_assessments',
    )
    assessment_number = models.CharField(max_length=50)
    assessment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    overall_risk_level = models.CharField(
        max_length=20, choices=RISK_LEVEL_CHOICES, default='low',
    )
    financial_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    geopolitical_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    compliance_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    operational_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assessed_risks',
        blank=True,
        null=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_risks',
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'assessment_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.assessment_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        if not self.assessment_number:
            last = SupplierRiskAssessment.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.assessment_number:
                try:
                    num = int(last.assessment_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.assessment_number = f"RA-{num:05d}"
        # Calculate overall risk score as average of dimension scores
        scores = [self.financial_risk_score, self.geopolitical_risk_score,
                  self.compliance_risk_score, self.operational_risk_score]
        non_zero = [s for s in scores if s > 0]
        if non_zero:
            self.overall_risk_score = sum(non_zero) / len(non_zero)
        super().save(*args, **kwargs)


class RiskFactor(models.Model):
    CATEGORY_CHOICES = [
        ('financial', 'Financial'),
        ('geopolitical', 'Geopolitical'),
        ('compliance', 'Compliance'),
        ('operational', 'Operational'),
        ('reputational', 'Reputational'),
        ('environmental', 'Environmental'),
    ]

    STATUS_CHOICES = [
        ('identified', 'Identified'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Accepted'),
        ('monitoring', 'Monitoring'),
    ]

    assessment = models.ForeignKey(
        SupplierRiskAssessment,
        on_delete=models.CASCADE,
        related_name='risk_factors',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    factor_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    likelihood = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    impact = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    mitigation_plan = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='identified')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['category', 'id']

    def __str__(self):
        return f"{self.factor_name} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        # Auto-calculate risk score: likelihood * impact * 4 (scales to 100)
        self.risk_score = self.likelihood * self.impact * 4
        super().save(*args, **kwargs)


class RiskMitigationAction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    risk_factor = models.ForeignKey(
        RiskFactor,
        on_delete=models.CASCADE,
        related_name='mitigation_actions',
    )
    action_description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_mitigation_actions',
        blank=True,
        null=True,
    )
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"Action: {self.action_description[:50]}"
