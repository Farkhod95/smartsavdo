from rest_framework import serializers
from suppliers.models import SupplierDebtRepayment
from suppliers.serializer.supplier import SupplierListSerializer


class SupplierDebtRepaymentListSerializer(serializers.ModelSerializer):
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)

    class Meta:
        model = SupplierDebtRepayment
        fields = ('id', 'supplier', 'supplier_detail', 'employee', 'date', 'total_debt_old', 'total_debt',
                  'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class SupplierDebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDebtRepayment
        fields = ('id', 'supplier', 'employee', 'date', 'total_debt_old', 'total_debt', 'summa_total_dollar',
                  'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')
