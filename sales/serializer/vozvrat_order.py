from rest_framework import serializers
from accounts.serializers import  FilialListSerializer
from sales.models import  VozvratOrder
from sales.serializer.client import ClientListSerializer


class VozvratOrderListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date',
                  'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete',
                  'is_vazvrat_status', 'is_karzinka')


class VozvratOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client',
                  'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
                  'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete', 'is_vazvrat_status', 'is_karzinka')
