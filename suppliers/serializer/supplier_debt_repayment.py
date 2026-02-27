from rest_framework import serializers
from decimal import Decimal
from suppliers.models import SupplierDebtRepayment
from suppliers.serializer.supplier import SupplierListSerializer
from users.serializers import UserViewListSerializer


class SupplierDebtRepaymentListSerializer(serializers.ModelSerializer):
    supplier_detail = SupplierListSerializer(source='supplier', read_only=True)
    employee_detail = UserViewListSerializer(source='employee', read_only=True)

    class Meta:
        model = SupplierDebtRepayment
        fields = ('id', 'supplier', 'supplier_detail', 'employee', 'employee_detail', 'date', 'total_debt_old', 'total_debt',
                  'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class SupplierDebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDebtRepayment
        fields = ('id', 'supplier', 'employee', 'date', 'total_debt_old', 'total_debt', 'summa_total_dollar',
                  'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class SupplierDebtRepaymentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDebtRepayment
        fields = (
            'id', 'supplier', 'employee', 'date',
            'total_debt_old', 'total_debt',
            'summa_total_dollar',
            'summa_dollar', 'summa_naqt', 'summa_kilik',
            'summa_terminal', 'summa_transfer'
        )
        read_only_fields = ('id', 'employee', 'total_debt_old', 'total_debt')

    def validate(self, attrs):
        # kamida bitta to'lov bo'lsin
        def d(x):
            try:
                return Decimal(x or 0)
            except Exception:
                return Decimal('0')

        paid_parts = (
            d(attrs.get('summa_dollar')) +
            d(attrs.get('summa_naqt')) +
            d(attrs.get('summa_kilik')) +
            d(attrs.get('summa_terminal')) +
            d(attrs.get('summa_transfer'))
        )
        paid_total = d(attrs.get('summa_total_dollar'))

        # agar total berilmagan bo'lsa — parts yig'indisini total deb olamiz
        if paid_total <= 0 and paid_parts > 0:
            attrs['summa_total_dollar'] = paid_parts
            paid_total = paid_parts

        if paid_total <= 0:
            raise serializers.ValidationError({"summa_total_dollar": "To‘lov summasi 0 dan katta bo‘lishi kerak."})

        return attrs