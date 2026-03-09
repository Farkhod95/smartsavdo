import django_filters
from django_filters import FilterSet
from sales.models import Client, ClientKeshbekHistory, Order, OrderHistory, OrderHistoryProduct, VozvratOrder


class ClientFilter(FilterSet):
    class Meta:
        model = Client
        fields = {
            'telegram_id': ['exact'],
            'full_name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'date_of_birthday': ['exact', 'gte', 'lte'],
            'gender': ['exact', 'icontains'],
            'phone_number': ['exact', 'icontains'],
            'region': ['exact'],
            'district': ['exact'],
            'filial': ['exact'],
            'total_debt': ['exact', 'gte', 'lte'],
            'keshbek': ['exact', 'gte', 'lte'],
            'is_profit_loss': ['exact'],
            'type': ['exact'],
            'is_delete': ['exact'],
        }


class ClientKeshbekHistoryFilter(FilterSet):
    class Meta:
        model = ClientKeshbekHistory
        fields = {
            'client': ['exact'],
            'keshbek': ['exact', 'gte', 'lte'],
            'keshbek_summa': ['exact', 'gte', 'lte'],
            'order_history': ['exact'],
        }


class OrderFilter(FilterSet):
    class Meta:
        model = Order
        fields = {
            'number_of_order': ['exact'],
            'client': ['exact'],
            'filial': ['exact'],
            # 'date_last_order': ['exact', 'gte', 'lte'],
            # 'all_profit_dollar': ['exact', 'gte', 'lte'],
            # 'total_debt_client': ['exact', 'gte', 'lte'],
            # 'total_debt_old_client': ['exact', 'gte', 'lte'],
            # 'all_product_summa': ['exact', 'gte', 'lte'],
            # 'summa_total_dollar': ['exact', 'gte', 'lte'],
            # 'summa_dollar': ['exact', 'gte', 'lte'],
            # 'summa_naqt': ['exact', 'gte', 'lte'],
            # 'summa_kilik': ['exact', 'gte', 'lte'],
            # 'summa_terminal': ['exact', 'gte', 'lte'],
            # 'summa_transfer': ['exact', 'gte', 'lte'],
            # 'discount_amount': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
        }


class OrderHistoryFilter(FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    filial = django_filters.NumberFilter(field_name='order_filial_id', lookup_expr='exact')
    class Meta:
        model = OrderHistory
        fields = {
            'order': ['exact'],
            'client': ['exact'],
            'employee': ['exact'],
            'currency': ['exact'],
            'created_by': ['exact'],
            'order_filial': ['exact'],
            'exchange_rate': ['exact', 'gte', 'lte'],
            'date': ['exact', 'gte', 'lte'],
            # 'all_profit_dollar': ['exact', 'gte', 'lte'],
            # 'total_debt_client': ['exact', 'gte', 'lte'],
            # 'total_debt_today_client': ['exact', 'gte', 'lte'],
            # 'all_product_summa': ['exact', 'gte', 'lte'],
            # 'summa_total_dollar': ['exact', 'gte', 'lte'],
            # 'summa_dollar': ['exact', 'gte', 'lte'],
            # 'summa_naqt': ['exact', 'gte', 'lte'],
            # 'summa_kilik': ['exact', 'gte', 'lte'],
            # 'summa_terminal': ['exact', 'gte', 'lte'],
            # 'summa_transfer': ['exact', 'gte', 'lte'],
            # 'discount_amount': ['exact', 'gte', 'lte'],
            # 'zdacha_dollar': ['exact', 'gte', 'lte'],
            # 'zdacha_som': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
            'order_status': ['exact'],
            'update_status': ['exact', 'gte', 'lte'],
            'is_debtor_product': ['exact'],
            'status_order_dukon': ['exact'],
            'status_order_sklad': ['exact'],
            'is_karzinka': ['exact'],
            'price_difference': ['exact'],
            'driver_info': ['exact', 'icontains'],
        }


class OrderHistoryProductFilter(FilterSet):
    class Meta:
        model = OrderHistoryProduct
        fields = {
            'date': ['exact', 'gte', 'lte'],
            'order_history': ['exact'],
            'product': ['exact'],
            'sklad': ['exact'],
            'vozvrat_order': ['exact'],
            'branch': ['exact'],
            'branch_category': ['exact'],
            'model': ['exact'],
            'type': ['exact'],
            'size': ['exact'],
            # 'count': ['exact', 'gte', 'lte'],
            # 'given_count': ['exact', 'gte', 'lte'],
            # 'real_price': ['exact', 'gte', 'lte'],
            # 'unit_price': ['exact', 'gte', 'lte'],
            # 'wholesale_price': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
            'is_karzinka': ['exact'],
            'cargo_terminal': ['exact', 'icontains'],
            'price_difference': ['exact'],
            'status_order': ['exact'],
        }


class VozvratOrderFilter(FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = VozvratOrder
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
            'is_delete': ['exact'],
            'is_vazvrat_status': ['exact'],
        }