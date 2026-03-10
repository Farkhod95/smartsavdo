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


class DebtRepaymentItemListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    client_full_name = serializers.CharField(allow_null=True, required=False)
    date = serializers.DateField(allow_null=True)
    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    old_total_debt_client = serializers.DecimalField(max_digits=20, decimal_places=2)


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


class SoldOrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    client_id = serializers.IntegerField(allow_null=True)
    client_name = serializers.CharField(allow_null=True)
    employee_id = serializers.IntegerField(allow_null=True)
    employee_name = serializers.CharField(allow_null=True)
    time = serializers.CharField(allow_null=True)
    datetime = serializers.DateTimeField(allow_null=True)
    note = serializers.CharField(allow_null=True)
    driver_info = serializers.CharField(allow_null=True)

    all_product_summa = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_naqt = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_kilik = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_terminal = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_transfer = serializers.DecimalField(max_digits=20, decimal_places=2)
    all_profit_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)


class DebtRepaymentItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    client_id = serializers.IntegerField(allow_null=True)
    client_name = serializers.CharField(allow_null=True)
    employee_id = serializers.IntegerField(allow_null=True)
    employee_name = serializers.CharField(allow_null=True)
    time = serializers.CharField(allow_null=True)
    datetime = serializers.DateTimeField(allow_null=True)
    note = serializers.CharField(allow_null=True)

    old_total_debt_client = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_debt_client = serializers.DecimalField(max_digits=20, decimal_places=2)
    paid_debt_dollar = serializers.DecimalField(source='summa_total_dollar', max_digits=20, decimal_places=2)

    summa_total_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_naqt = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_kilik = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_terminal = serializers.DecimalField(max_digits=20, decimal_places=2)
    summa_transfer = serializers.DecimalField(max_digits=20, decimal_places=2)


class OrdersAndDebtsReportRowSerializer(serializers.Serializer):
    row_number = serializers.IntegerField()
    type = serializers.CharField()
    object_id = serializers.IntegerField()

    client_id = serializers.IntegerField(allow_null=True)
    client_name = serializers.CharField(allow_null=True)

    employee_id = serializers.IntegerField(allow_null=True)
    employee_name = serializers.CharField(allow_null=True)

    all_product_summa = serializers.CharField()
    all_profit_dollar = serializers.CharField()
    total_debt_client = serializers.CharField()

    summa_total_dollar = serializers.CharField()
    summa_dollar = serializers.CharField()
    summa_naqt = serializers.CharField()
    summa_kilik = serializers.CharField()
    summa_terminal = serializers.CharField()
    summa_transfer = serializers.CharField()
    discount_amount = serializers.CharField()
    zdacha_dollar = serializers.CharField()

    vaqti = serializers.CharField(allow_null=True)
    holati = serializers.CharField()
    datetime = serializers.DateTimeField(allow_null=True)


class OrdersTotalsSerializer(serializers.Serializer):
    all_profit_dollar = serializers.CharField()
    summa_total_dollar = serializers.CharField()
    summa_dollar = serializers.CharField()
    summa_naqt = serializers.CharField()
    summa_kilik = serializers.CharField()
    summa_terminal = serializers.CharField()
    summa_transfer = serializers.CharField()
    discount_amount = serializers.CharField()
    zdacha_dollar = serializers.CharField()


class DebtsTotalsSerializer(serializers.Serializer):
    summa_total_dollar = serializers.CharField()
    summa_dollar = serializers.CharField()
    summa_naqt = serializers.CharField()
    summa_kilik = serializers.CharField()
    summa_terminal = serializers.CharField()
    summa_transfer = serializers.CharField()
    discount_amount = serializers.CharField()
    zdacha_dollar = serializers.CharField()


class OrdersAndDebtsTotalsSerializer(serializers.Serializer):
    totalproduct_summa = serializers.CharField()
    totalprofit = serializers.CharField()
    total_all_qarz = serializers.CharField()
    orders = OrdersTotalsSerializer()
    debts = DebtsTotalsSerializer()


class OrdersAndDebtsReportGroupSerializer(serializers.Serializer):
    date = serializers.DateField()
    date_label = serializers.CharField()
    count = serializers.IntegerField()
    totals = OrdersAndDebtsTotalsSerializer()
    items = OrdersAndDebtsReportRowSerializer(many=True)