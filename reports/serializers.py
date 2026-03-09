# reports/serializers.py
from rest_framework import serializers

class DebtorClientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(allow_null=True, required=False)
    phone_number = serializers.CharField(allow_null=True, required=False)
    total_debt = serializers.DecimalField(max_digits=20, decimal_places=2)
    keshbek = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_order_date = serializers.DateField(allow_null=True)


class OrderHistoryItemSerializer(serializers.Serializer):
    client_full_name = serializers.CharField(allow_null=True, required=False)
    date = serializers.DateField(allow_null=True)
    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    all_product_summa = serializers.DecimalField(max_digits=20, decimal_places=2)


class DebtRepaymentItemSerializer(serializers.Serializer):
    client_full_name = serializers.CharField(allow_null=True, required=False)
    date = serializers.DateField(allow_null=True)
    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)


class ExpenseItemSerializer(serializers.Serializer):
    date = serializers.DateField(allow_null=True)
    category_name = serializers.CharField(allow_null=True, required=False)

    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_naqt = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_kilik = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_terminal = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_transfer = serializers.DecimalField(max_digits=20, decimal_places=2)


class MoneyTotalsSerializer(serializers.Serializer):
    # ko‘p joyda ishlatamiz (OrderHistory / DebtRepayment / Expense total)
    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_naqt = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_kilik = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_terminal = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_transfer = serializers.DecimalField(max_digits=20, decimal_places=2)


class OrderHistoryTotalsSerializer(MoneyTotalsSerializer):
    all_product_summa = serializers.DecimalField(max_digits=20, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    zdacha_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    zdacha_som = serializers.DecimalField(max_digits=20, decimal_places=2)


class DebtRepaymentTotalsSerializer(MoneyTotalsSerializer):
    discount_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    zdacha_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    zdacha_som = serializers.DecimalField(max_digits=20, decimal_places=2)


class ExpenseTotalsSerializer(MoneyTotalsSerializer):
    pass


class OrderDebtHistoryResponseSerializer(serializers.Serializer):
    filters = serializers.DictField()

    orders = serializers.DictField()
    repayments = serializers.DictField()
    expenses = serializers.DictField()


class TopClientItemSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    client_full_name = serializers.CharField(allow_null=True, required=False)

    order_count = serializers.IntegerField()

    sum_summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    sum_all_product_summa = serializers.DecimalField(max_digits=20, decimal_places=2)
    sum_all_profit_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)


class SoldProductsHistorySerializer(serializers.Serializer):
    date = serializers.DateField(source='created_date')
    date_label = serializers.SerializerMethodField()

    orders_count = serializers.IntegerField()
    all_product_summa = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    all_profit_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)

    def get_date_label(self, obj):
        date_value = obj.get("created_date")
        if not date_value:
            return None
        return date_value.strftime("%d.%m.%Y")