from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# COMMON CHOICES
# =============================================================================

TRANSPORT_MODE_CHOICES = [
    ('road', 'Road'),
    ('air', 'Air'),
    ('ocean', 'Ocean'),
    ('rail', 'Rail'),
    ('multimodal', 'Multimodal'),
]

CURRENCY_CHOICES = [
    ('USD', 'USD - US Dollar'),
    ('EUR', 'EUR - Euro'),
    ('GBP', 'GBP - British Pound'),
    ('PKR', 'PKR - Pakistani Rupee'),
    ('AED', 'AED - UAE Dirham'),
    ('SAR', 'SAR - Saudi Riyal'),
    ('INR', 'INR - Indian Rupee'),
    ('CNY', 'CNY - Chinese Yuan'),
]

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
]


# =============================================================================
# CARRIER MANAGEMENT
# =============================================================================

class Carrier(models.Model):
    CARRIER_TYPE_CHOICES = [
        ('ftl', 'Full Truckload (FTL)'),
        ('ltl', 'Less Than Truckload (LTL)'),
        ('parcel', 'Parcel'),
        ('air_freight', 'Air Freight'),
        ('ocean_freight', 'Ocean Freight'),
        ('rail', 'Rail'),
        ('courier', 'Courier'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='tms_carriers',
    )
    carrier_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    carrier_type = models.CharField(
        max_length=20, choices=CARRIER_TYPE_CHOICES, default='ftl',
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'carrier_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.carrier_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.carrier_number:
            last = Carrier.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.carrier_number:
                try:
                    num = int(last.carrier_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.carrier_number = f"CAR-{num:05d}"
        super().save(*args, **kwargs)


class RateCard(models.Model):
    UNIT_TYPE_CHOICES = [
        ('per_kg', 'Per Kg'),
        ('per_cbm', 'Per CBM'),
        ('per_pallet', 'Per Pallet'),
        ('per_container', 'Per Container'),
        ('flat_rate', 'Flat Rate'),
        ('per_mile', 'Per Mile'),
        ('per_km', 'Per Km'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='tms_rate_cards',
    )
    rate_number = models.CharField(max_length=50)
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        related_name='rate_cards',
    )
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    transport_mode = models.CharField(
        max_length=20, choices=TRANSPORT_MODE_CHOICES, default='road',
    )
    rate_per_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    unit_type = models.CharField(
        max_length=20, choices=UNIT_TYPE_CHOICES, default='per_kg',
    )
    min_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transit_days = models.IntegerField(default=0)
    effective_from = models.DateField()
    effective_to = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'rate_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rate_number} - {self.carrier.name} ({self.origin} → {self.destination})"

    def save(self, *args, **kwargs):
        if not self.rate_number:
            last = RateCard.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.rate_number:
                try:
                    num = int(last.rate_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.rate_number = f"RC-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# ROUTE PLANNING
# =============================================================================

class Route(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='tms_routes',
    )
    route_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_time_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.SET_NULL,
        related_name='routes',
        blank=True,
        null=True,
    )
    transport_mode = models.CharField(
        max_length=20, choices=TRANSPORT_MODE_CHOICES, default='road',
    )
    waypoints = models.TextField(blank=True, help_text='Comma-separated waypoints')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    fuel_cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    toll_cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'route_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.route_number} - {self.name}"

    @property
    def total_cost_estimate(self):
        return self.fuel_cost_estimate + self.toll_cost_estimate

    def save(self, *args, **kwargs):
        if not self.route_number:
            last = Route.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.route_number:
                try:
                    num = int(last.route_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.route_number = f"RT-{num:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# SHIPMENT TRACKING
# =============================================================================

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('booked', 'Booked'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('at_hub', 'At Hub'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='tms_shipments',
    )
    shipment_number = models.CharField(max_length=50)
    order = models.ForeignKey(
        'oms.Order',
        on_delete=models.SET_NULL,
        related_name='shipments',
        blank=True,
        null=True,
    )
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        related_name='shipments',
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.SET_NULL,
        related_name='shipments',
        blank=True,
        null=True,
    )
    origin_address = models.TextField()
    destination_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    transport_mode = models.CharField(
        max_length=20, choices=TRANSPORT_MODE_CHOICES, default='road',
    )
    estimated_departure = models.DateTimeField(blank=True, null=True)
    actual_departure = models.DateTimeField(blank=True, null=True)
    estimated_arrival = models.DateTimeField(blank=True, null=True)
    actual_arrival = models.DateTimeField(blank=True, null=True)
    total_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tracking_url = models.URLField(blank=True)
    current_location = models.CharField(max_length=255, blank=True)
    special_instructions = models.TextField(blank=True)
    shipped_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tms_shipments',
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'shipment_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shipment_number} - {self.carrier.name}"

    def save(self, *args, **kwargs):
        if not self.shipment_number:
            last = Shipment.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.shipment_number:
                try:
                    num = int(last.shipment_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.shipment_number = f"SHP-{num:05d}"
        super().save(*args, **kwargs)


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='shipment_items',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


class ShipmentTracking(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_events',
    )
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    notes = models.CharField(max_length=500, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tms_tracking_events',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.shipment.shipment_number} - {self.location} ({self.get_status_display()})"


# =============================================================================
# FREIGHT AUDIT & PAYMENT
# =============================================================================

class FreightBill(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('disputed', 'Disputed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='tms_freight_bills',
    )
    bill_number = models.CharField(max_length=50)
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='freight_bills',
    )
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        related_name='freight_bills',
    )
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    audited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tms_audited_bills',
        blank=True,
        null=True,
    )
    audited_at = models.DateTimeField(blank=True, null=True)
    dispute_reason = models.TextField(blank=True)
    payment_date = models.DateField(blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'bill_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bill_number} - {self.carrier.name}"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            last = FreightBill.objects.filter(
                tenant=self.tenant
            ).order_by('-id').first()
            if last and last.bill_number:
                try:
                    num = int(last.bill_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.bill_number = f"FB-{num:05d}"
        super().save(*args, **kwargs)


class FreightBillItem(models.Model):
    CHARGE_TYPE_CHOICES = [
        ('base_freight', 'Base Freight'),
        ('fuel_surcharge', 'Fuel Surcharge'),
        ('handling', 'Handling'),
        ('insurance', 'Insurance'),
        ('customs', 'Customs'),
        ('toll', 'Toll'),
        ('accessorial', 'Accessorial'),
        ('other', 'Other'),
    ]

    freight_bill = models.ForeignKey(
        FreightBill,
        on_delete=models.CASCADE,
        related_name='items',
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    charge_type = models.CharField(
        max_length=20, choices=CHARGE_TYPE_CHOICES, default='base_freight',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description} - {self.total_price}"


# =============================================================================
# LOAD OPTIMIZATION
# =============================================================================

class LoadPlan(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('truck_20ft', '20ft Truck'),
        ('truck_40ft', '40ft Truck'),
        ('container_20ft', '20ft Container'),
        ('container_40ft', '40ft Container'),
        ('van', 'Van'),
        ('flatbed', 'Flatbed'),
        ('refrigerated', 'Refrigerated'),
        ('bulk', 'Bulk Carrier'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('loading', 'Loading'),
        ('loaded', 'Loaded'),
        ('closed', 'Closed'),
    ]

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='tms_load_plans',
    )
    plan_number = models.CharField(max_length=50)
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.SET_NULL,
        related_name='load_plans',
        blank=True,
        null=True,
    )
    vehicle_type = models.CharField(
        max_length=20, choices=VEHICLE_TYPE_CHOICES, default='truck_20ft',
    )
    max_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    planned_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    planned_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    utilization_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    planned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tms_load_plans',
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'plan_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan_number} - {self.get_vehicle_type_display()}"

    def calculate_utilization(self):
        if self.max_weight > 0:
            weight_util = (self.planned_weight / self.max_weight) * 100
        else:
            weight_util = 0
        if self.max_volume > 0:
            volume_util = (self.planned_volume / self.max_volume) * 100
        else:
            volume_util = 0
        self.utilization_percent = max(weight_util, volume_util)

    def save(self, *args, **kwargs):
        if not self.plan_number:
            last = LoadPlan.objects.filter(
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
        self.calculate_utilization()
        super().save(*args, **kwargs)


class LoadPlanItem(models.Model):
    load_plan = models.ForeignKey(
        LoadPlan,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item = models.ForeignKey(
        'procurement.Item',
        on_delete=models.CASCADE,
        related_name='load_plan_items',
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    load_sequence = models.IntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['load_sequence', 'id']

    def __str__(self):
        return f"{self.item.name} x {self.quantity} (Seq: {self.load_sequence})"
