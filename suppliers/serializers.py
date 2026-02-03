from rest_framework import serializers

from accounts.serializers import FilialListSerializer, SkladListSerializer, RegionListSerializer, \
    DistrictListPublicSerializer
from suppliers.models import PurchaseInvoice, Supplier, SupplierAccount, SupplierDebtRepayment


class SupplierListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    class Meta:
        model = Supplier
        fields = ('id', 'name', 'filial', 'filial_detail', 'region', 'region_detail', 'district', 'district_detail', 'address', 'inn', 'note', 'is_active', 'is_delete')


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('id', 'name', 'filial', 'region', 'district', 'address', 'inn', 'note', 'is_active', 'is_delete')


class SupplierAccountListSerializer(serializers.ModelSerializer):
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)

    class Meta:
        model = SupplierAccount
        fields = ('id', 'supplier', 'supplier_detail', 'total_turnover', 'filial_debt')


class SupplierAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAccount
        fields = ('id', 'supplier', 'total_turnover', 'filial_debt')


class SupplierDebtRepaymentListSerializer(serializers.ModelSerializer):
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)

    class Meta:
        model = SupplierDebtRepayment
        fields = ('id', 'supplier', 'supplier_detail', 'employee', 'date', 'total_debt_old', 'total_debt', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class SupplierDebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDebtRepayment
        fields = ('id', 'supplier', 'employee', 'date', 'total_debt_old', 'total_debt', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class PurchaseInvoiceListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)
    sklad_detail = SkladListSerializer(source='sklad', read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = ('id', 'type', 'employee', 'supplier', 'supplier_detail', 'filial', 'filial_detail', 'sklad', 'sklad_detail', 'date', 'total_debt_old', 'total_debt', 'total_debt_today', 'product_count', 'all_product_summa', 'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt', 'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer')


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoice
        fields = ('id', 'type', 'employee', 'supplier', 'filial', 'sklad', 'date', 'total_debt_old', 'total_debt', 'total_debt_today', 'product_count', 'all_product_summa', 'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt', 'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer')