from rest_framework import serializers
from decimal import Decimal

from accounts.serializers import FilialListSerializer, SkladListSerializer
from suppliers.models import PurchaseInvoice, SupplierAccount
from suppliers.serializer.supplier import SupplierListSerializer


class PurchaseInvoiceListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)
    sklad_detail = SkladListSerializer(source='sklad', read_only=True)
    supplier_debt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = ('id', 'type', 'employee', 'supplier', 'supplier_detail', 'filial', 'filial_detail', 'sklad',
                  'sklad_detail', 'date', 'total_debt_old', 'total_debt', 'total_debt_today', 'product_count',
                  'all_product_summa', 'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt',
                  'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer', 'is_karzinka')

    def get_supplier_debt(self, obj):
        if not obj.supplier_id:
            return Decimal('0.00')

        account = (
            SupplierAccount.objects
            .filter(supplier_id=obj.supplier_id)
            .only('filial_debt')
            .first()
        )

        if not account or account.filial_debt is None:
            return Decimal('0.00')

        return account.filial_debt


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    supplier_debt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = (
            'id', 'type', 'employee', 'supplier', 'filial', 'sklad', 'date',
            'total_debt_old', 'total_debt', 'total_debt_today',
            'product_count', 'all_product_summa',
            'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt',
            'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer',
            'is_karzinka',
            'supplier_debt',  # ✅ doim ko‘rinadi
        )

    def get_supplier_debt(self, obj):
        if not obj.supplier_id:
            return Decimal('0.00')

        account = (
            SupplierAccount.objects
            .filter(supplier_id=obj.supplier_id)
            .only('filial_debt')
            .first()
        )

        if not account or account.filial_debt is None:
            return Decimal('0.00')

        return account.filial_debt