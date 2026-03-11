import django_filters
from django_filters import FilterSet

from suppliers.models import PurchaseInvoice, Supplier, SupplierAccount, SupplierDebtRepayment


class SupplierFilter(FilterSet):
    class Meta:
        model = Supplier
        fields = {
            'name': ['exact', 'icontains'],
            'type': ['exact'],
            'filial': ['exact'],
            'region': ['exact'],
            'district': ['exact'],
            'inn': ['exact'],
            'is_active': ['exact'],
            'is_delete': ['exact'],
        }


class SupplierAccountFilter(FilterSet):
    class Meta:
        model = SupplierAccount
        fields = {
            'supplier': ['exact'],
            'total_turnover': ['exact', 'gte', 'lte'],
            'filial_debt': ['exact', 'gte', 'lte'],
        }


class SupplierDebtRepaymentFilter(FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = SupplierDebtRepayment
        fields = {
            'supplier': ['exact'],
            'employee': ['exact'],
            'date': ['exact', 'gte', 'lte'],
            'total_debt_old': ['exact', 'gte', 'lte'],
            'total_debt': ['exact', 'gte', 'lte'],
            'summa_total_dollar': ['exact', 'gte', 'lte'],
            'summa_dollar': ['exact', 'gte', 'lte'],
            'summa_naqt': ['exact', 'gte', 'lte'],
            'summa_kilik': ['exact', 'gte', 'lte'],
            'summa_terminal': ['exact', 'gte', 'lte'],
            'summa_transfer': ['exact', 'gte', 'lte'],
        }


class PurchaseInvoiceFilter(FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = PurchaseInvoice
        fields = {
            'type': ['exact'],
            'is_karzinka': ['exact'],
            'employee': ['exact'],
            'supplier': ['exact'],
            'sklad_outgoing': ['exact'],
            'filial': ['exact'],
            'sklad': ['exact'],
            'is_confirm': ['exact'],
            'date': ['exact', 'gte', 'lte'],
            'total_debt_old': ['exact', 'gte', 'lte'],
            'total_debt': ['exact', 'gte', 'lte'],
            'total_debt_today': ['exact', 'gte', 'lte'],
            'product_count': ['exact', 'gte', 'lte'],
            'all_product_summa': ['exact', 'gte', 'lte'],
            'given_summa_total_dollar': ['exact', 'gte', 'lte'],
            'given_summa_dollar': ['exact', 'gte', 'lte'],
            'given_summa_naqt': ['exact', 'gte', 'lte'],
            'given_summa_kilik': ['exact', 'gte', 'lte'],
            'given_summa_terminal': ['exact', 'gte', 'lte'],
            'given_summa_transfer': ['exact', 'gte', 'lte'],
        }