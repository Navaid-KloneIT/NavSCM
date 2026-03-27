from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# INSPECTION TEMPLATES
# =============================================================================

class InspectionTemplate(models.Model):
    INSPECTION_TYPE_CHOICES = [
        ('incoming', 'Incoming'),
        ('in_process', 'In-Process'),
        ('final', 'Final'),
        ('outgoing', 'Outgoing'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='inspection_templates',
    )
    name = models.CharField(max_length=255)
    inspection_type = models.CharField(
        max_length=20, choices=INSPECTION_TYPE_CHOICES, default='incoming',
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_inspection_templates',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class InspectionCriteria(models.Model):
    MEASUREMENT_TYPE_CHOICES = [
        ('visual', 'Visual'),
        ('dimensional', 'Dimensional'),
        ('functional', 'Functional'),
        ('chemical', 'Chemical'),
        ('electrical', 'Electrical'),
        ('mechanical', 'Mechanical'),
    ]

    template = models.ForeignKey(
        InspectionTemplate,
        on_delete=models.CASCADE,
        related_name='criteria',
    )
    sequence = models.PositiveIntegerField(default=10)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    acceptance_criteria = models.TextField(blank=True)
    measurement_type = models.CharField(
        max_length=20, choices=MEASUREMENT_TYPE_CHOICES, default='visual',
    )
    is_required = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Inspection Criteria'
        verbose_name_plural = 'Inspection Criteria'
        ordering = ['sequence', 'id']

    def __str__(self):
        return f"{self.sequence}: {self.name}"


# =============================================================================
# QUALITY INSPECTIONS
# =============================================================================

class QualityInspection(models.Model):
    INSPECTION_TYPE_CHOICES = [
        ('incoming', 'Incoming'),
        ('in_process', 'In-Process'),
        ('final', 'Final'),
        ('outgoing', 'Outgoing'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('on_hold', 'On Hold'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='quality_inspections',
    )
    inspection_number = models.CharField(max_length=50)
    template = models.ForeignKey(
        InspectionTemplate,
        on_delete=models.SET_NULL,
        related_name='inspections',
        blank=True,
        null=True,
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='quality_inspections',
    )
    work_order = models.ForeignKey(
        'manufacturing.WorkOrder',
        on_delete=models.SET_NULL,
        related_name='quality_inspections',
        blank=True,
        null=True,
    )
    inspection_type = models.CharField(
        max_length=20, choices=INSPECTION_TYPE_CHOICES, default='incoming',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_inspections',
        blank=True,
        null=True,
    )
    inspection_date = models.DateField(blank=True, null=True)
    lot_number = models.CharField(max_length=100, blank=True)
    sample_size = models.PositiveIntegerField(default=1)
    accepted_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_quality_inspections',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'inspection_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.inspection_number} - {self.item.name}"

    def save(self, *args, **kwargs):
        if not self.inspection_number:
            last = QualityInspection.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.inspection_number:
                try:
                    num = int(last.inspection_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.inspection_number = f"QI-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def pass_rate(self):
        total = self.results.count()
        if total > 0:
            passed = self.results.filter(result='pass').count()
            return round((passed / total) * 100, 1)
        return 0

    @property
    def total_results(self):
        return self.results.count()

    @property
    def passed_results(self):
        return self.results.filter(result='pass').count()

    @property
    def failed_results(self):
        return self.results.filter(result='fail').count()


class InspectionResult(models.Model):
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning'),
        ('na', 'N/A'),
    ]

    inspection = models.ForeignKey(
        QualityInspection,
        on_delete=models.CASCADE,
        related_name='results',
    )
    criteria = models.ForeignKey(
        InspectionCriteria,
        on_delete=models.SET_NULL,
        related_name='results',
        blank=True,
        null=True,
    )
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='pass')
    measured_value = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        criteria_name = self.criteria.name if self.criteria else 'N/A'
        return f"{criteria_name}: {self.get_result_display()}"


# =============================================================================
# NON-CONFORMANCE REPORTS
# =============================================================================

class NonConformanceReport(models.Model):
    SOURCE_CHOICES = [
        ('incoming_inspection', 'Incoming Inspection'),
        ('in_process', 'In-Process'),
        ('final_inspection', 'Final Inspection'),
        ('customer_complaint', 'Customer Complaint'),
        ('supplier_issue', 'Supplier Issue'),
        ('internal_audit', 'Internal Audit'),
    ]

    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('under_investigation', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]

    DISPOSITION_CHOICES = [
        ('use_as_is', 'Use As-Is'),
        ('rework', 'Rework'),
        ('scrap', 'Scrap'),
        ('return_to_supplier', 'Return to Supplier'),
        ('sort_and_segregate', 'Sort and Segregate'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='ncrs',
    )
    ncr_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='ncrs',
        blank=True,
        null=True,
    )
    work_order = models.ForeignKey(
        'manufacturing.WorkOrder',
        on_delete=models.SET_NULL,
        related_name='ncrs',
        blank=True,
        null=True,
    )
    inspection = models.ForeignKey(
        QualityInspection,
        on_delete=models.SET_NULL,
        related_name='ncrs',
        blank=True,
        null=True,
    )
    source = models.CharField(
        max_length=30, choices=SOURCE_CHOICES, default='incoming_inspection',
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='minor',
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    disposition = models.CharField(
        max_length=25, choices=DISPOSITION_CHOICES, blank=True,
    )
    disposition_notes = models.TextField(blank=True)
    quantity_affected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reported_ncrs',
        blank=True,
        null=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_ncrs',
        blank=True,
        null=True,
    )
    reported_date = models.DateField(blank=True, null=True)
    closed_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_ncrs',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Non-Conformance Report'
        verbose_name_plural = 'Non-Conformance Reports'
        unique_together = ('tenant', 'ncr_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ncr_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.ncr_number:
            last = NonConformanceReport.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.ncr_number:
                try:
                    num = int(last.ncr_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.ncr_number = f"NCR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def days_open(self):
        if self.closed_date:
            delta = self.closed_date - self.reported_date if self.reported_date else None
            return delta.days if delta else 0
        if self.reported_date:
            return (timezone.now().date() - self.reported_date).days
        return 0


# =============================================================================
# CORRECTIVE & PREVENTIVE ACTIONS (CAPA)
# =============================================================================

class CAPA(models.Model):
    CAPA_TYPE_CHOICES = [
        ('corrective', 'Corrective'),
        ('preventive', 'Preventive'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('verification', 'Verification'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='capas',
    )
    capa_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    capa_type = models.CharField(
        max_length=15, choices=CAPA_TYPE_CHOICES, default='corrective',
    )
    ncr = models.ForeignKey(
        NonConformanceReport,
        on_delete=models.SET_NULL,
        related_name='capas',
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    description = models.TextField(blank=True)
    root_cause_analysis = models.TextField(blank=True)
    due_date = models.DateField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_capas',
        blank=True,
        null=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='verified_capas',
        blank=True,
        null=True,
    )
    verification_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_capas',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CAPA'
        verbose_name_plural = 'CAPAs'
        unique_together = ('tenant', 'capa_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.capa_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.capa_number:
            last = CAPA.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.capa_number:
                try:
                    num = int(last.capa_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.capa_number = f"CAPA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_date and not self.completed_date:
            return timezone.now().date() > self.due_date
        return False

    @property
    def action_count(self):
        return self.actions.count()

    @property
    def completed_action_count(self):
        return self.actions.filter(status='completed').count()


class CAPAAction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    capa = models.ForeignKey(
        CAPA,
        on_delete=models.CASCADE,
        related_name='actions',
    )
    sequence = models.PositiveIntegerField(default=10)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_capa_actions',
        blank=True,
        null=True,
    )
    due_date = models.DateField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['sequence', 'id']

    def __str__(self):
        return f"Action {self.sequence}: {self.description[:50]}"


# =============================================================================
# QUALITY AUDITS
# =============================================================================

class QualityAudit(models.Model):
    AUDIT_TYPE_CHOICES = [
        ('internal', 'Internal'),
        ('external', 'External'),
        ('supplier', 'Supplier'),
        ('process', 'Process'),
        ('product', 'Product'),
        ('system', 'System'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='quality_audits',
    )
    audit_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    audit_type = models.CharField(
        max_length=20, choices=AUDIT_TYPE_CHOICES, default='internal',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scope = models.TextField(blank=True)
    lead_auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='led_audits',
        blank=True,
        null=True,
    )
    audit_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    findings_summary = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_quality_audits',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quality Audit'
        verbose_name_plural = 'Quality Audits'
        unique_together = ('tenant', 'audit_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.audit_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.audit_number:
            last = QualityAudit.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.audit_number:
                try:
                    num = int(last.audit_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.audit_number = f"QA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_findings(self):
        return self.findings.count()

    @property
    def open_findings(self):
        return self.findings.filter(status='open').count()


class AuditFinding(models.Model):
    FINDING_TYPE_CHOICES = [
        ('observation', 'Observation'),
        ('minor_nc', 'Minor Non-Conformance'),
        ('major_nc', 'Major Non-Conformance'),
        ('opportunity_for_improvement', 'Opportunity for Improvement'),
        ('positive', 'Positive'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    audit = models.ForeignKey(
        QualityAudit,
        on_delete=models.CASCADE,
        related_name='findings',
    )
    finding_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    finding_type = models.CharField(
        max_length=30, choices=FINDING_TYPE_CHOICES, default='observation',
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='low',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_audit_findings',
        blank=True,
        null=True,
    )
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    corrective_action = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['finding_number', 'id']

    def __str__(self):
        return f"Finding {self.finding_number}: {self.title}"


# =============================================================================
# CERTIFICATE OF ANALYSIS
# =============================================================================

class CertificateOfAnalysis(models.Model):
    UOM_CHOICES = [
        ('piece', 'Piece'), ('kg', 'Kilogram'), ('g', 'Gram'),
        ('liter', 'Liter'), ('ml', 'Milliliter'), ('meter', 'Meter'),
        ('cm', 'Centimeter'), ('box', 'Box'), ('pack', 'Pack'),
        ('set', 'Set'), ('hour', 'Hour'), ('day', 'Day'), ('unit', 'Unit'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='coas',
    )
    coa_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='coas',
    )
    batch_number = models.CharField(max_length=100, blank=True)
    production_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_of_measure = models.CharField(
        max_length=20, choices=UOM_CHOICES, default='piece',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_coas',
        blank=True,
        null=True,
    )
    approved_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_coas',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Certificate of Analysis'
        verbose_name_plural = 'Certificates of Analysis'
        unique_together = ('tenant', 'coa_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.coa_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.coa_number:
            last = CertificateOfAnalysis.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.coa_number:
                try:
                    num = int(last.coa_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.coa_number = f"COA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_tests(self):
        return self.test_results.count()

    @property
    def passed_tests(self):
        return self.test_results.filter(status='pass').count()

    @property
    def all_tests_passed(self):
        total = self.test_results.count()
        if total == 0:
            return False
        return self.test_results.filter(status='pass').count() == total


class CoATestResult(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    coa = models.ForeignKey(
        CertificateOfAnalysis,
        on_delete=models.CASCADE,
        related_name='test_results',
    )
    sequence = models.PositiveIntegerField(default=10)
    test_name = models.CharField(max_length=255)
    test_method = models.CharField(max_length=255, blank=True)
    specification = models.CharField(max_length=255, blank=True)
    result = models.CharField(max_length=255, blank=True)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pass')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['sequence', 'id']

    def __str__(self):
        return f"{self.sequence}: {self.test_name} - {self.get_status_display()}"
