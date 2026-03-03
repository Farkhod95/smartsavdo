from rest_framework import serializers
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from accounts.serializers import FilialListSerializer
from finance.models import Expense
from finance.serializer.expense_category import ExpenseCategoryListSerializer
from users.serializers import UserViewListSerializer


class ExpenseListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    category_detail = ExpenseCategoryListSerializer(source='category', read_only=True)
    employee_detail = UserViewListSerializer(source='employee', read_only=True)

    class Meta:
        model = Expense
        fields = ('id', 'filial', 'filial_detail', 'category', 'category_detail', 'is_salary', 'employee', 'employee_detail', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete', 'exchange_rate')


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ('id', 'filial', 'category', 'is_salary', 'employee', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
                  'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete', 'exchange_rate')


Q2 = Decimal("0.01")
Q6 = Decimal("0.000001")

MONEY_FIELDS = ("summa_dollar", "summa_naqt", "summa_kilik", "summa_terminal", "summa_transfer")


def d(v) -> Decimal:
    if v is None or v == "":
        return Decimal("0")
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def q2(v: Decimal) -> Decimal:
    return v.quantize(Q2, rounding=ROUND_HALF_UP)


def q6(v: Decimal) -> Decimal:
    return v.quantize(Q6, rounding=ROUND_HALF_UP)


class ExpenseWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = (
            "id",
            "filial",
            "category",
            "is_salary",
            "employee",
            "exchange_rate",
            "summa_total_dollar",  # front yuborsa ham qayta hisoblanadi
            "summa_dollar",
            "summa_naqt",
            "summa_kilik",
            "summa_terminal",
            "summa_transfer",
            "date",
            "note",
            "is_delete",
        )
        extra_kwargs = {"summa_total_dollar": {"required": False}}

    def validate(self, attrs):
        inst = getattr(self, "instance", None)

        # Kurs 6 xonada (model shunaqa), lekin natijalar 2 xonada bo'ladi
        rate = q6(d(attrs.get("exchange_rate", inst.exchange_rate if inst else 0)))
        if rate < 0:
            raise serializers.ValidationError({"exchange_rate": "Kurs manfiy bo‘lishi mumkin emas."})

        vals = {}
        for f in MONEY_FIELDS:
            vals[f] = q2(d(attrs.get(f, getattr(inst, f) if inst else 0)))
            if vals[f] < 0:
                raise serializers.ValidationError({f: "Qiymat manfiy bo‘lishi mumkin emas."})

        uzs_total = vals["summa_naqt"] + vals["summa_kilik"] + vals["summa_terminal"] + vals["summa_transfer"]

        # UZS -> USD (kurs > 0 bo'lsa)
        uzs_usd = Decimal("0.00")
        if rate > 0:
            uzs_usd = q2(uzs_total / rate)  # 2 xonaga darhol

        # Yakuniy total ham 2 xonada
        total_usd = q2(vals["summa_dollar"] + uzs_usd)

        # Saqlanadigan qiymatlar
        attrs["exchange_rate"] = rate
        for f in MONEY_FIELDS:
            attrs[f] = vals[f]
        attrs["summa_total_dollar"] = total_usd

        return attrs