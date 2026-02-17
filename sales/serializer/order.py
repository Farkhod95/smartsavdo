from rest_framework import serializers
from accounts.serializers import FilialListSerializer
from sales.models import Order
from sales.serializer.client import ClientListSerializer


class OrderListSerializer(serializers.ModelSerializer):
    client_detail = ClientListSerializer(source='client', read_only=True)
    filial_detail = FilialListSerializer(source='filial', read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'number_of_order', 'client', 'client_detail', 'filial', 'filial_detail', 'date_last_order',
                  'all_profit_dollar', 'total_debt_client', 'total_debt_old_client', 'all_product_summa',
                  'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer',
                  'discount_amount', 'is_delete')


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'number_of_order', 'client', 'filial', 'date_last_order', 'all_profit_dollar', 'total_debt_client',
                  'total_debt_old_client', 'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt',
                  'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete')


