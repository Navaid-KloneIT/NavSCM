from django.conf import settings
from django.db import models


# =============================================================================
# SALES FORECASTING
# =============================================================================

class SalesForecast(models.Model):
    FORECAST_METHOD_CHOICES = [
        ('moving_average', 'Moving Average'),
        ('exponential_smoothing', 'Exponential Smoothing'),
        ('linear_regression', 'Linear Regression'),
        ('manual', 'Manual Entry'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='sales_forecasts',
    )
    forecast_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    forecast_method = models.CharField(
        max_length=30, choices=FORECAST_METHOD_CHOICES, default='moving_average',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_forecasts',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_forecasts',
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'forecast_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.forecast_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.forecast_number:
            last = SalesForecast.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.forecast_number:
                try:
                    num = int(last.forecast_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.forecast_number = f"FC-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_forecasted(self):
        return sum(item.forecasted_quantity for item in self.items.all())

    @property
    def total_actual(self):
        return sum(
            item.actual_quantity for item in self.items.all()
            if item.actual_quantity is not None
        )


class ForecastLineItem(models.Model):
    forecast = models.ForeignKey(
        SalesForecast,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='forecast_items',
        blank=True,
        null=True,
    )
    forecasted_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
    )
    confidence_level = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Confidence level percentage (0-100)',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name if self.item else 'N/A'} - {self.forecasted_quantity}"

    @property
    def variance(self):
        if self.actual_quantity is not None:
            return self.actual_quantity - self.forecasted_quantity
        return None

    @property
    def variance_percentage(self):
        if self.actual_quantity is not None and self.forecasted_quantity:
            return (
                (self.actual_quantity - self.forecasted_quantity)
                / self.forecasted_quantity * 100
            )
        return None


# =============================================================================
# SEASONALITY ANALYSIS
# =============================================================================

class SeasonalityProfile(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='seasonality_profiles',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='seasonality_profiles',
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    jan_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    feb_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    mar_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    apr_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    may_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    jun_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    jul_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    aug_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    sep_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    oct_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    nov_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    dec_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_seasonality_profiles',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'item')
        ordering = ['item__name']

    def __str__(self):
        return f"{self.name} ({self.item.name})"

    def get_factor_for_month(self, month):
        month_fields = [
            'jan_factor', 'feb_factor', 'mar_factor', 'apr_factor',
            'may_factor', 'jun_factor', 'jul_factor', 'aug_factor',
            'sep_factor', 'oct_factor', 'nov_factor', 'dec_factor',
        ]
        return getattr(self, month_fields[month - 1])


class PromotionalEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('holiday', 'Holiday'),
        ('promotion', 'Promotion'),
        ('clearance', 'Clearance'),
        ('launch', 'Product Launch'),
        ('seasonal', 'Seasonal'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='promotional_events',
    )
    seasonality_profile = models.ForeignKey(
        SeasonalityProfile,
        on_delete=models.CASCADE,
        related_name='events',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, default='promotion',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    impact_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.00,
        help_text='Multiplier for demand during this event (e.g. 1.5 = 50% increase)',
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_promotional_events',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()})"


# =============================================================================
# DEMAND SENSING
# =============================================================================

class DemandSignal(models.Model):
    SIGNAL_TYPE_CHOICES = [
        ('market_trend', 'Market Trend'),
        ('competitor_action', 'Competitor Action'),
        ('weather', 'Weather'),
        ('economic_indicator', 'Economic Indicator'),
        ('social_media', 'Social Media'),
        ('customer_feedback', 'Customer Feedback'),
        ('pos_data', 'POS Data'),
    ]

    IMPACT_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('analyzed', 'Analyzed'),
        ('incorporated', 'Incorporated'),
        ('dismissed', 'Dismissed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='demand_signals',
    )
    signal_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    signal_type = models.CharField(
        max_length=30, choices=SIGNAL_TYPE_CHOICES, default='market_trend',
    )
    impact_level = models.CharField(
        max_length=20, choices=IMPACT_LEVEL_CHOICES, default='medium',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='demand_signals',
        blank=True,
        null=True,
        help_text='Specific item affected, if applicable',
    )
    estimated_impact_pct = models.DecimalField(
        max_digits=7, decimal_places=2, default=0,
        help_text='Estimated demand impact percentage (positive=increase, negative=decrease)',
    )
    signal_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_demand_signals',
        blank=True,
        null=True,
    )
    analyzed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='analyzed_demand_signals',
        blank=True,
        null=True,
    )
    analyzed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'signal_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.signal_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.signal_number:
            last = DemandSignal.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.signal_number:
                try:
                    num = int(last.signal_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.signal_number = f"DS-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# COLLABORATIVE PLANNING
# =============================================================================

class CollaborativePlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('sales_plan', 'Sales Plan'),
        ('marketing_plan', 'Marketing Plan'),
        ('finance_plan', 'Finance Plan'),
        ('operations_plan', 'Operations Plan'),
        ('consensus', 'Consensus Plan'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('finalized', 'Finalized'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='collaborative_plans',
    )
    plan_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    plan_type = models.CharField(
        max_length=20, choices=PLAN_TYPE_CHOICES, default='sales_plan',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    forecast = models.ForeignKey(
        SalesForecast,
        on_delete=models.SET_NULL,
        related_name='collaborative_plans',
        blank=True,
        null=True,
        help_text='Linked sales forecast, if any',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_collaborative_plans',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_collaborative_plans',
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'plan_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.plan_number:
            last = CollaborativePlan.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.plan_number:
                try:
                    num = int(last.plan_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.plan_number = f"CP-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def total_planned_quantity(self):
        return sum(item.planned_quantity for item in self.items.all())


class PlanLineItem(models.Model):
    plan = models.ForeignKey(
        CollaborativePlan,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='plan_items',
        blank=True,
        null=True,
    )
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name if self.item else 'N/A'} - {self.planned_quantity}"


class PlanComment(models.Model):
    plan = models.ForeignKey(
        CollaborativePlan,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='plan_comments',
        blank=True,
        null=True,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.plan.plan_number}"


# =============================================================================
# SAFETY STOCK CALCULATION
# =============================================================================

class SafetyStockCalculation(models.Model):
    CALCULATION_METHOD_CHOICES = [
        ('fixed', 'Fixed Quantity'),
        ('percentage', 'Percentage of Demand'),
        ('statistical', 'Statistical (Z-score)'),
        ('demand_based', 'Demand-Based'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('applied', 'Applied'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='safety_stock_calculations',
    )
    calculation_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    calculation_method = models.CharField(
        max_length=20, choices=CALCULATION_METHOD_CHOICES, default='statistical',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    calculation_date = models.DateField()
    default_service_level = models.DecimalField(
        max_digits=5, decimal_places=2, default=95.00,
        help_text='Default service level percentage (e.g. 95.00)',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_safety_stock_calcs',
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_safety_stock_calcs',
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'calculation_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.calculation_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.calculation_number:
            last = SafetyStockCalculation.objects.filter(
                tenant=self.tenant
            ).order_by('-created_at').first()
            if last and last.calculation_number:
                try:
                    num = int(last.calculation_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.calculation_number = f"SS-{num:05d}"
        super().save(*args, **kwargs)


class SafetyStockItem(models.Model):
    calculation = models.ForeignKey(
        SafetyStockCalculation,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='safety_stock_items',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='safety_stock_items',
    )
    avg_demand = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Average daily/weekly demand',
    )
    demand_std_dev = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Standard deviation of demand',
    )
    lead_time_days = models.PositiveIntegerField(default=0)
    lead_time_std_dev = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text='Standard deviation of lead time in days',
    )
    service_level_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=95.00,
    )
    calculated_safety_stock = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
    )
    current_stock = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
    )
    recommended_reorder_point = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('calculation', 'item', 'warehouse')
        ordering = ['item__name']

    def __str__(self):
        return f"{self.item.name} @ {self.warehouse.name} - SS: {self.calculated_safety_stock}"
