from django.contrib import admin

from finance.models import ExchangeRate, ExpenseCategory, Expense, DebtRepayment, ExchangeRateHistory


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'filial', 'dollar', 'is_active')
    fields = ('filial', 'dollar', 'is_active')
    search_fields = ('filial__name',)
    list_filter = ('filial',)


@admin.register(ExchangeRateHistory)
class ExchangeRateHistoryAdmin(admin.ModelAdmin):
    list_display = ('filial', 'exchange_rate', 'old_dollar', 'new_dollar')
    list_select_related = ('filial', 'exchange_rate')
    list_filter = ('filial',)
    search_fields = ('filial__name',)
    fields = ('exchange_rate', 'old_dollar', 'new_dollar', 'filial')


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    fields = ('name',)
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'filial', 'category', 'is_salary', 'employee', 'date', 'summa_total_dollar', 'summa_dollar',
                    'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'is_delete', 'exchange_rate')
    fields = ('filial', 'category', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal',
              'summa_transfer', 'date', 'note', 'is_delete', 'exchange_rate')
    search_fields = ('filial__name', 'category__name', 'note')
    list_filter = ('is_delete', 'date', 'filial', 'category')


@admin.register(DebtRepayment)
class DebtRepaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'filial', 'client', 'employee', 'date', 'summa_total_dollar', 'total_debt_client', 'debt_status', 'is_delete')
    fields = ('filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'debt_status')
    search_fields = ('client__full_name', 'employee__username', 'note')
    list_filter = ('is_delete', 'debt_status', 'date', 'filial', 'employee')
