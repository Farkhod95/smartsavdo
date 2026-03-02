import django_filters
from django_filters import FilterSet

from finance.models import ExchangeRate, ExpenseCategory, Expense, DebtRepayment, ExchangeRateHistory


class ExchangeRateFilter(FilterSet):
    class Meta:
        model = ExchangeRate
        fields = {
            'filial': ['exact'],
            'dollar': ['exact', 'gte', 'lte'],
        }


class ExpenseCategoryFilter(FilterSet):
    class Meta:
        model = ExpenseCategory
        fields = {
            'name': ['exact', 'icontains'],
        }


class ExpenseFilter(FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Expense
        fields = {
            'filial': ['exact'],
            'category': ['exact'],
            'is_salary': ['exact'],
            'employee': ['exact'],
            # 'summa_total_dollar': ['exact', 'gte', 'lte'],
            # 'summa_dollar': ['exact', 'gte', 'lte'],
            # 'summa_naqt': ['exact', 'gte', 'lte'],
            # 'summa_kilik': ['exact', 'gte', 'lte'],
            # 'summa_terminal': ['exact', 'gte', 'lte'],
            # 'summa_transfer': ['exact', 'gte', 'lte'],
            'date': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
        }


class DebtRepaymentFilter(FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = DebtRepayment
        fields = {
            'filial': ['exact'],
            'client': ['exact'],
            'employee': ['exact'],
            'exchange_rate': ['exact', 'gte', 'lte'],
            'date': ['exact', 'gte', 'lte'],
            # 'old_total_debt_client': ['exact', 'gte', 'lte'],
            # 'total_debt_client': ['exact', 'gte', 'lte'],
            # 'summa_total_dollar': ['exact', 'gte', 'lte'],
            # 'summa_dollar': ['exact', 'gte', 'lte'],
            # 'summa_naqt': ['exact', 'gte', 'lte'],
            # 'summa_kilik': ['exact', 'gte', 'lte'],
            # 'summa_terminal': ['exact', 'gte', 'lte'],
            # 'summa_transfer': ['exact', 'gte', 'lte'],
            'discount_amount': ['exact', 'gte', 'lte'],
            'zdacha_dollar': ['exact', 'gte', 'lte'],
            'zdacha_som': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
            'debt_status': ['exact'],
        }


class ExchangeRateHistoryFilter(FilterSet):
    old_dollar_from = django_filters.NumberFilter(field_name='old_dollar', lookup_expr='gte')
    old_dollar_to = django_filters.NumberFilter(field_name='old_dollar', lookup_expr='lte')
    new_dollar_from = django_filters.NumberFilter(field_name='new_dollar', lookup_expr='gte')
    new_dollar_to = django_filters.NumberFilter(field_name='new_dollar', lookup_expr='lte')

    class Meta:
        model = ExchangeRateHistory
        fields = ('exchange_rate', 'filial', 'old_dollar', 'new_dollar')