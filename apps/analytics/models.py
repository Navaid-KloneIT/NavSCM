from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# INVENTORY ANALYTICS
# =============================================================================

class InventoryAnalytics(models.Model):
    REPORT_TYPE_CHOICES = [
        ('turnover_analysis', 'Turnover Analysis'),
        ('dead_stock', 'Dead Stock'),
        ('aging_inventory', 'Aging Inventory'),
        ('stock_summary', 'Stock Summary'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='inventory_analytics',
    )
    report_number = models.CharField(max_length=50)
    report_type = models.CharField(
        max_length=30, choices=REPORT_TYPE_CHOICES, default='stock_summary',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    total_items = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    turnover_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    dead_stock_count = models.IntegerField(default=0)
    dead_stock_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    aging_30_count = models.IntegerField(default=0)
    aging_60_count = models.IntegerField(default=0)
    aging_90_count = models.IntegerField(default=0)
    aging_90_plus_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_inventory_analytics',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventory Analytics Report'
        verbose_name_plural = 'Inventory Analytics Reports'
        unique_together = ('tenant', 'report_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.get_report_type_display()}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            last = InventoryAnalytics.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.report_number:
                try:
                    num = int(last.report_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.report_number = f"INV-RPT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()


class InventoryAnalyticsItem(models.Model):
    report = models.ForeignKey(
        InventoryAnalytics,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='inventory_analytics_items',
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='inventory_analytics_items',
    )
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    days_since_last_movement = models.IntegerField(default=0)
    turnover_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_dead_stock = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} @ {self.warehouse.name}"


# =============================================================================
# PROCUREMENT ANALYTICS
# =============================================================================

class ProcurementAnalytics(models.Model):
    REPORT_TYPE_CHOICES = [
        ('spend_analysis', 'Spend Analysis'),
        ('vendor_performance', 'Vendor Performance'),
        ('cost_savings', 'Cost Savings'),
        ('purchase_summary', 'Purchase Summary'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='procurement_analytics',
    )
    report_number = models.CharField(max_length=50)
    report_type = models.CharField(
        max_length=30, choices=REPORT_TYPE_CHOICES, default='spend_analysis',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    total_spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    avg_order_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rejection_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    top_vendor_spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_procurement_analytics',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Procurement Analytics Report'
        verbose_name_plural = 'Procurement Analytics Reports'
        unique_together = ('tenant', 'report_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.get_report_type_display()}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            last = ProcurementAnalytics.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.report_number:
                try:
                    num = int(last.report_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.report_number = f"PRC-RPT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()


class ProcurementAnalyticsItem(models.Model):
    report = models.ForeignKey(
        ProcurementAnalytics,
        on_delete=models.CASCADE,
        related_name='items',
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        related_name='procurement_analytics_items',
    )
    total_spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    order_count = models.IntegerField(default=0)
    avg_lead_time_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rejection_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_variance = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.vendor.name} - {self.total_spend}"


# =============================================================================
# LOGISTICS KPIs
# =============================================================================

class LogisticsKPI(models.Model):
    REPORT_TYPE_CHOICES = [
        ('delivery_performance', 'Delivery Performance'),
        ('freight_cost', 'Freight Cost'),
        ('vehicle_utilization', 'Vehicle Utilization'),
        ('carrier_performance', 'Carrier Performance'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='logistics_kpis',
    )
    report_number = models.CharField(max_length=50)
    report_type = models.CharField(
        max_length=30, choices=REPORT_TYPE_CHOICES, default='delivery_performance',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    total_shipments = models.IntegerField(default=0)
    on_time_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_freight_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_cost_per_shipment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_transit_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    vehicle_utilization_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_logistics_kpis',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Logistics KPI Report'
        verbose_name_plural = 'Logistics KPI Reports'
        unique_together = ('tenant', 'report_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.get_report_type_display()}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            last = LogisticsKPI.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.report_number:
                try:
                    num = int(last.report_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.report_number = f"LOG-KPI-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()


class LogisticsKPIItem(models.Model):
    report = models.ForeignKey(
        LogisticsKPI,
        on_delete=models.CASCADE,
        related_name='items',
    )
    carrier = models.ForeignKey(
        'tms.Carrier',
        on_delete=models.CASCADE,
        related_name='logistics_kpi_items',
    )
    shipment_count = models.IntegerField(default=0)
    on_time_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_cost_per_shipment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_transit_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.carrier} - {self.shipment_count} shipments"


# =============================================================================
# FINANCIAL REPORTING
# =============================================================================

class FinancialReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('gross_margin', 'Gross Margin'),
        ('cost_breakdown', 'Cost Breakdown'),
        ('revenue_analysis', 'Revenue Analysis'),
        ('profitability', 'Profitability'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='financial_reports',
    )
    report_number = models.CharField(max_length=50)
    report_type = models.CharField(
        max_length=30, choices=REPORT_TYPE_CHOICES, default='gross_margin',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_cogs = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gross_margin = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gross_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    procurement_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    logistics_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    manufacturing_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    warehousing_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_financial_reports',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Financial Report'
        verbose_name_plural = 'Financial Reports'
        unique_together = ('tenant', 'report_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.get_report_type_display()}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            last = FinancialReport.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.report_number:
                try:
                    num = int(last.report_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.report_number = f"FIN-RPT-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()


class FinancialReportItem(models.Model):
    report = models.ForeignKey(
        FinancialReport,
        on_delete=models.CASCADE,
        related_name='items',
    )
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    percentage_of_total = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.category} - {self.amount}"


# =============================================================================
# PREDICTIVE ANALYTICS
# =============================================================================

class PredictiveAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('demand_spike', 'Demand Spike'),
        ('supply_disruption', 'Supply Disruption'),
        ('stockout_risk', 'Stockout Risk'),
        ('price_fluctuation', 'Price Fluctuation'),
        ('delivery_delay', 'Delivery Delay'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('analyzing', 'Analyzing'),
        ('confirmed', 'Confirmed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='predictive_alerts',
    )
    alert_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    alert_type = models.CharField(
        max_length=25, choices=ALERT_TYPE_CHOICES, default='stockout_risk',
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='medium',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new')
    description = models.TextField(blank=True)
    affected_item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.SET_NULL,
        related_name='predictive_alerts',
        blank=True,
        null=True,
    )
    affected_vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.SET_NULL,
        related_name='predictive_alerts',
        blank=True,
        null=True,
    )
    predicted_date = models.DateField(blank=True, null=True)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    impact_description = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='resolved_alerts',
        blank=True,
        null=True,
    )
    resolved_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_predictive_alerts',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Predictive Alert'
        verbose_name_plural = 'Predictive Alerts'
        unique_together = ('tenant', 'alert_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.alert_number:
            last = PredictiveAlert.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.alert_number:
                try:
                    num = int(last.alert_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.alert_number = f"PA-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def days_since_created(self):
        return (timezone.now().date() - self.created_at.date()).days
