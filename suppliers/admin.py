from django.contrib import admin

from suppliers.models import PurchaseInvoice, Supplier, SupplierAccount, SupplierDebtRepayment


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'filial', 'region', 'district', 'inn', 'is_active', 'is_delete')
    fields = ('name', 'filial', 'region', 'district', 'address', 'inn', 'note', 'is_active', 'is_delete')
    search_fields = ('name', 'inn', 'address')
    list_filter = ('is_active', 'is_delete', 'filial', 'region', 'district')


@admin.register(SupplierAccount)
class SupplierAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'total_turnover', 'filial_debt')
    fields = ('supplier', 'total_turnover', 'filial_debt')
    search_fields = ('supplier__name',)
    list_filter = ('supplier',)


@admin.register(SupplierDebtRepayment)
class SupplierDebtRepaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'employee', 'date', 'total_debt_old', 'total_debt', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')
    fields = ('supplier', 'employee', 'date', 'total_debt_old', 'total_debt', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')
    search_fields = ('supplier__name', 'employee__username')
    list_filter = ('date', 'supplier', 'employee')


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'employee', 'supplier', 'filial', 'sklad', 'date', 'product_count', 'all_product_summa', 'total_debt', 'total_debt_today')
    fields = ('type', 'employee', 'supplier', 'filial', 'sklad', 'date', 'total_debt_old', 'total_debt', 'total_debt_today', 'product_count', 'all_product_summa', 'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt', 'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer')
    search_fields = ('supplier__name', 'filial__name', 'sklad__name', 'employee__username')
    list_filter = ('type', 'date', 'filial', 'sklad', 'supplier')