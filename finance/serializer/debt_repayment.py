from rest_framework import serializers

from accounts.serializers import FilialListSerializer
from finance.models import DebtRepayment
from sales.serializer.client import ClientListSerializer

class DebtRepaymentListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = DebtRepayment
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date',
                  'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar',
                  'zdacha_som', 'is_delete', 'debt_status')


class DebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtRepayment
        fields = ('id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client',
                  'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
                  'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som',
                  'is_delete', 'debt_status')


