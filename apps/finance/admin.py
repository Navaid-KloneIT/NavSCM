from django.contrib import admin

from .models import (
    APInvoice,
    APInvoiceItem,
    APPayment,
    ARInvoice,
    ARInvoiceItem,
    ARPayment,
    Budget,
    BudgetEntry,
    LandedCostComponent,
    LandedCostSheet,
    TaxRate,
    TaxTransaction,
)


# =============================================================================
# Accounts Payable
# =============================================================================

class APInvoiceItemInline(admin.TabularInline):
    model = APInvoiceItem
    extra = 1


@admin.register(APInvoice)
class APInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'vendor', 'status', 'total_amount', 'amount_paid', 'currency', 'due_date', 'tenant')
    list_filter = ('status', 'currency', 'tenant')
    search_fields = ('invoice_number',)
    inlines = [APInvoiceItemInline]


@admin.register(APPayment)
class APPaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'invoice', 'amount', 'payment_method', 'payment_date', 'tenant')
    list_filter = ('payment_method', 'tenant')
    search_fields = ('payment_number', 'reference_number')


# =============================================================================
# Accounts Receivable
# =============================================================================

class ARInvoiceItemInline(admin.TabularInline):
    model = ARInvoiceItem
    extra = 1


@admin.register(ARInvoice)
class ARInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'status', 'total_amount', 'amount_received', 'currency', 'due_date', 'tenant')
    list_filter = ('status', 'currency', 'tenant')
    search_fields = ('invoice_number',)
    inlines = [ARInvoiceItemInline]


@admin.register(ARPayment)
class ARPaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'invoice', 'amount', 'payment_method', 'payment_date', 'tenant')
    list_filter = ('payment_method', 'tenant')
    search_fields = ('payment_number', 'reference_number')


# =============================================================================
# Landed Cost
# =============================================================================

class LandedCostComponentInline(admin.TabularInline):
    model = LandedCostComponent
    extra = 1


@admin.register(LandedCostSheet)
class LandedCostSheetAdmin(admin.ModelAdmin):
    list_display = ('sheet_number', 'status', 'total_goods_cost', 'total_landed_cost', 'currency', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('sheet_number',)
    inlines = [LandedCostComponentInline]


# =============================================================================
# Budgeting
# =============================================================================

class BudgetEntryInline(admin.TabularInline):
    model = BudgetEntry
    extra = 1


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('budget_number', 'name', 'department', 'status', 'planned_amount', 'actual_amount', 'currency', 'tenant')
    list_filter = ('status', 'period_type', 'tenant')
    search_fields = ('budget_number', 'name', 'department')
    inlines = [BudgetEntryInline]


# =============================================================================
# Tax Management
# =============================================================================

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'tax_type', 'rate', 'is_active', 'country', 'tenant')
    list_filter = ('tax_type', 'is_active', 'tenant')
    search_fields = ('code', 'name')


@admin.register(TaxTransaction)
class TaxTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_number', 'transaction_type', 'taxable_amount', 'tax_amount', 'transaction_date', 'tenant')
    list_filter = ('transaction_type', 'tenant')
    search_fields = ('transaction_number', 'reference_number')
