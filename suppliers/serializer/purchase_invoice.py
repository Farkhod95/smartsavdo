from rest_framework import serializers
from decimal import Decimal

from accounts.serializers import FilialSerializer, SkladForSerializer
from suppliers.models import PurchaseInvoice, SupplierAccount
from suppliers.serializer.supplier import SupplierSerializer
from users.serializers import UserViewListSerializer


class PurchaseInvoiceListSerializer(serializers.ModelSerializer):
    filial_detail = FilialSerializer(source='filial', read_only=True)
    employee_detail = UserViewListSerializer(source='employee', read_only=True)
    sklad_outgoing_detail = SkladForSerializer(source='sklad_outgoing', read_only=True)
    supplier_detail = SupplierSerializer(source='supplier', read_only=True)
    sklad_detail = SkladForSerializer(source='sklad', read_only=True)
    supplier_debt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = ('id', 'type', 'employee', 'employee_detail', 'supplier', 'supplier_detail', 'sklad_outgoing', 'sklad_outgoing_detail',
                  'filial', 'filial_detail', 'sklad', 'sklad_detail', 'date', 'total_debt_old', 'total_debt',
                  'total_debt_today', 'product_count',
                  'all_product_summa', 'given_summa_total_dollar', 'given_summa_dollar', 'given_summa_naqt',
                  'given_summa_kilik', 'given_summa_terminal', 'given_summa_transfer', 'is_karzinka', 'supplier_debt')

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
            'id', 'type', 'employee', 'supplier', 'sklad_outgoing', 'filial', 'sklad', 'date',
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





class PurchaseInvoiceDoneSerializer(serializers.ModelSerializer):
    supplier_debt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = (
            'id', 'type', 'employee', 'supplier',
            'sklad_outgoing', 'filial', 'sklad', 'date',

            'total_debt_old', 'total_debt', 'total_debt_today',
            'product_count', 'all_product_summa',

            'given_summa_total_dollar',
            'given_summa_dollar', 'given_summa_naqt', 'given_summa_kilik',
            'given_summa_terminal', 'given_summa_transfer',

            'is_karzinka',
            'supplier_debt',
        )
        read_only_fields = (
            # done endpoint’da avtomatik hisoblanadiganlar
            'total_debt_old', 'total_debt', 'total_debt_today',
            'product_count', 'all_product_summa',
            'is_karzinka',
            'supplier_debt',
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

    def validate(self, attrs):
        """
        DONE endpoint: minimal tekshiruvlar.
        INTERNAL bo'lsa sklad_outgoing shart (transfer).
        """
        instance: PurchaseInvoice = self.instance
        invoice_type = instance.type  # serializerda read-only qoldirdik
        if invoice_type == PurchaseInvoice.TYPE.INTERNAL and not instance.sklad_outgoing_id:
            raise serializers.ValidationError({"sklad_outgoing": "Ichki kirim (transfer) uchun chiqish sklad majburiy."})
        if not instance.filial_id:
            raise serializers.ValidationError({"filial": "Invoice’da filial tanlanmagan."})
        if not instance.sklad_id:
            raise serializers.ValidationError({"sklad": "Invoice’da kiruvchi sklad tanlanmagan."})
        return attrs