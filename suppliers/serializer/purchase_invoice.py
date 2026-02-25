from rest_framework import serializers

from accounts.serializers import FilialListSerializer, SkladListSerializer
from suppliers.models import PurchaseInvoice
from suppliers.serializer.supplier import SupplierListSerializer


class PurchaseInvoiceListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)
    sklad_detail = SkladListSerializer(source='sklad', read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = ('id', 'type', 'employee', 'supplier', 'supplier_detail', 'filial', 'filial_detail', 'sklad',
                  'sklad_detail', 'date', 'total_debt_old', 'total_debt', 'total_debt_today', 'product_count',
                  'all_product_summa', 'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt',
                  'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer', 'is_karzinka')


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoice
        fields = ('id', 'type', 'employee', 'supplier', 'filial', 'sklad', 'date', 'total_debt_old', 'total_debt',
                  'total_debt_today', 'product_count', 'all_product_summa', 'given_summa_total_dollar',
                  'given_summa_dollar', 'given_summa_naqt', 'given_summa_kilik', 'given_summa_terminal',
                  'given_summa_transfer', 'is_karzinka')