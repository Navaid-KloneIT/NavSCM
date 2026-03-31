from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# LABOR PLANNING
# =============================================================================

class LaborPlan(models.Model):
    DEPARTMENT_CHOICES = [
        ('receiving', 'Receiving'),
        ('picking', 'Picking'),
        ('packing', 'Packing'),
        ('shipping', 'Shipping'),
        ('loading', 'Loading'),
        ('inventory', 'Inventory Control'),
        ('general', 'General'),
    ]

    SHIFT_CHOICES = [
        ('morning', 'Morning (6AM-2PM)'),
        ('afternoon', 'Afternoon (2PM-10PM)'),
        ('night', 'Night (10PM-6AM)'),
        ('flexible', 'Flexible'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='labor_plans',
    )
    plan_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        related_name='labor_plans',
        blank=True,
        null=True,
    )
    department = models.CharField(
        max_length=20, choices=DEPARTMENT_CHOICES, default='general',
    )
    shift = models.CharField(
        max_length=20, choices=SHIFT_CHOICES, default='morning',
    )
    plan_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    expected_inbound_volume = models.PositiveIntegerField(default=0)
    expected_outbound_volume = models.PositiveIntegerField(default=0)
    required_headcount = models.PositiveIntegerField(default=0)
    available_headcount = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_labor_plans',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Labor Plan'
        verbose_name_plural = 'Labor Plans'
        unique_together = ('tenant', 'plan_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.plan_number:
            last = LaborPlan.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.plan_number:
                try:
                    num = int(last.plan_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.plan_number = f"LP-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def headcount_gap(self):
        return self.required_headcount - self.available_headcount

    @property
    def is_understaffed(self):
        return self.available_headcount < self.required_headcount

    @property
    def total_volume(self):
        return self.expected_inbound_volume + self.expected_outbound_volume

    @property
    def line_count(self):
        return self.plan_lines.count()


class LaborPlanLine(models.Model):
    plan = models.ForeignKey(
        LaborPlan,
        on_delete=models.CASCADE,
        related_name='plan_lines',
    )
    role = models.CharField(max_length=100)
    required_count = models.PositiveIntegerField(default=0)
    available_count = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.role} - Required: {self.required_count}"


# =============================================================================
# TIME & ATTENDANCE
# =============================================================================

class Attendance(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning (6AM-2PM)'),
        ('afternoon', 'Afternoon (2PM-10PM)'),
        ('night', 'Night (10PM-6AM)'),
        ('flexible', 'Flexible'),
    ]

    STATUS_CHOICES = [
        ('clocked_in', 'Clocked In'),
        ('on_break', 'On Break'),
        ('clocked_out', 'Clocked Out'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    attendance_number = models.CharField(max_length=50)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        related_name='attendance_records',
        blank=True,
        null=True,
    )
    date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='clocked_in')
    shift = models.CharField(
        max_length=20, choices=SHIFT_CHOICES, default='morning',
    )
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(blank=True, null=True)
    break_start = models.DateTimeField(blank=True, null=True)
    break_end = models.DateTimeField(blank=True, null=True)
    break_duration_minutes = models.PositiveIntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    standard_hours_per_day = models.DecimalField(
        max_digits=4, decimal_places=2, default=8,
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_attendance',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        unique_together = ('tenant', 'attendance_number')
        ordering = ['-date', '-clock_in']

    def __str__(self):
        return f"{self.attendance_number} - {self.worker}"

    def save(self, *args, **kwargs):
        if not self.attendance_number:
            last = Attendance.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.attendance_number:
                try:
                    num = int(last.attendance_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.attendance_number = f"ATT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_hours(self):
        if self.clock_in and self.clock_out:
            return round((self.clock_out - self.clock_in).total_seconds() / 3600, 2)
        return 0

    @property
    def net_hours(self):
        return round(self.total_hours - (self.break_duration_minutes / 60), 2)

    @property
    def overtime_hours_calculated(self):
        return max(0, round(self.net_hours - float(self.standard_hours_per_day), 2))


# =============================================================================
# TASK ASSIGNMENT
# =============================================================================

class TaskAssignment(models.Model):
    TASK_TYPE_CHOICES = [
        ('picking', 'Picking'),
        ('packing', 'Packing'),
        ('receiving', 'Receiving'),
        ('loading', 'Loading'),
        ('putaway', 'Put Away'),
        ('counting', 'Cycle Counting'),
        ('cleaning', 'Cleaning'),
        ('replenishment', 'Replenishment'),
        ('other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='task_assignments',
    )
    task_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    task_type = models.CharField(
        max_length=20, choices=TASK_TYPE_CHOICES, default='picking',
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        related_name='task_assignments',
        blank=True,
        null=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        blank=True,
        null=True,
    )
    assigned_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    estimated_duration_minutes = models.PositiveIntegerField(default=0)
    actual_duration_minutes = models.PositiveIntegerField(default=0)
    units_to_process = models.PositiveIntegerField(default=0)
    units_processed = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_task_assignments',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Task Assignment'
        verbose_name_plural = 'Task Assignments'
        unique_together = ('tenant', 'task_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.task_number:
            last = TaskAssignment.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.task_number:
                try:
                    num = int(last.task_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.task_number = f"TA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ('completed', 'cancelled'):
            return timezone.now().date() > self.due_date
        return False

    @property
    def duration_hours(self):
        if self.started_at and self.completed_at:
            return round((self.completed_at - self.started_at).total_seconds() / 3600, 2)
        return 0

    @property
    def units_per_hour(self):
        if self.duration_hours > 0:
            return round(self.units_processed / self.duration_hours, 2)
        return 0

    @property
    def accuracy_rate(self):
        if self.units_processed > 0:
            return round(((self.units_processed - self.errors_count) / self.units_processed) * 100, 2)
        return 100

    @property
    def checklist_count(self):
        return self.checklist_items.count()


class TaskChecklistItem(models.Model):
    task = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name='checklist_items',
    )
    item_name = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        status = 'Done' if self.is_completed else 'Pending'
        return f"{self.item_name} - {status}"


# =============================================================================
# PERFORMANCE TRACKING
# =============================================================================

class PerformanceReview(models.Model):
    RATING_CHOICES = [
        ('exceptional', 'Exceptional'),
        ('exceeds_expectations', 'Exceeds Expectations'),
        ('meets_expectations', 'Meets Expectations'),
        ('needs_improvement', 'Needs Improvement'),
        ('unsatisfactory', 'Unsatisfactory'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='performance_reviews',
    )
    review_number = models.CharField(max_length=50)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_reviews',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        related_name='performance_reviews',
        blank=True,
        null=True,
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    tasks_completed = models.PositiveIntegerField(default=0)
    total_units_processed = models.PositiveIntegerField(default=0)
    total_hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_errors = models.PositiveIntegerField(default=0)
    rating = models.CharField(
        max_length=25, choices=RATING_CHOICES, default='meets_expectations',
    )
    reviewer_comments = models.TextField(blank=True)
    worker_comments = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='conducted_reviews',
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_performance_reviews',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Performance Review'
        verbose_name_plural = 'Performance Reviews'
        unique_together = ('tenant', 'review_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.review_number} - {self.worker}"

    def save(self, *args, **kwargs):
        if not self.review_number:
            last = PerformanceReview.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.review_number:
                try:
                    num = int(last.review_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.review_number = f"PR-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def units_per_hour(self):
        if self.total_hours_worked > 0:
            return round(self.total_units_processed / float(self.total_hours_worked), 2)
        return 0

    @property
    def accuracy_rate(self):
        if self.total_units_processed > 0:
            return round(
                ((self.total_units_processed - self.total_errors) / self.total_units_processed) * 100, 2
            )
        return 100

    @property
    def overall_score(self):
        uph_normalized = min(self.units_per_hour, 100)
        return round((uph_normalized * 0.5) + (self.accuracy_rate * 0.5), 2)

    @property
    def period_days(self):
        if self.period_start and self.period_end:
            return (self.period_end - self.period_start).days
        return 0


# =============================================================================
# PAYROLL INTEGRATION
# =============================================================================

class PayrollRecord(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('PKR', 'PKR'),
        ('AED', 'AED'), ('SAR', 'SAR'), ('INR', 'INR'), ('CNY', 'CNY'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('exported', 'Exported'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='payroll_records',
    )
    payroll_number = models.CharField(max_length=50)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payroll_records',
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    regular_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    regular_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
    )
    days_worked = models.PositiveIntegerField(default=0)
    days_absent = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    exported_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_payroll_records',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payroll Record'
        verbose_name_plural = 'Payroll Records'
        unique_together = ('tenant', 'payroll_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payroll_number} - {self.worker}"

    def save(self, *args, **kwargs):
        if not self.payroll_number:
            last = PayrollRecord.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.payroll_number:
                try:
                    num = int(last.payroll_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.payroll_number = f"PAY-{num:05d}"
        # Auto-calculate pay amounts
        self.total_hours = self.regular_hours + self.overtime_hours
        self.regular_pay = self.regular_hours * self.hourly_rate
        self.overtime_pay = self.overtime_hours * self.overtime_rate
        super().save(*args, **kwargs)

    @property
    def gross_pay(self):
        return self.regular_pay + self.overtime_pay + self.bonuses

    @property
    def net_pay(self):
        return self.gross_pay - self.deductions

    @property
    def is_exported(self):
        return self.exported_at is not None
