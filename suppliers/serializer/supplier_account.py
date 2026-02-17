from rest_framework import serializers

from suppliers.models import SupplierAccount
from suppliers.serializer.supplier import SupplierListSerializer


class SupplierAccountListSerializer(serializers.ModelSerializer):
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)

    class Meta:
        model = SupplierAccount
        fields = ('id', 'supplier', 'supplier_detail', 'total_turnover', 'filial_debt')


class SupplierAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAccount
        fields = ('id', 'supplier', 'total_turnover', 'filial_debt')