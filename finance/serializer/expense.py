# finance/serializer/expense.py

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from rest_framework import serializers

from accounts.serializers import FilialListSerializer
from finance.models import Expense
from finance.serializer.expense_category import ExpenseCategoryListSerializer
from users.serializers import UserViewListSerializer


Q = Decimal("0.01")  # 2 decimal precision


def _d(val) -> Decimal:
    """
    Safe Decimal convert.
    None/"" -> 0
    """
    if val is None or val == "":
        return Decimal("0")
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _q2(val: Decimal) -> Decimal:
    """
    Quantize to 2 decimals with HALF_UP rounding.
    """
    return val.quantize(Q, rounding=ROUND_HALF_UP)


MONEY_FIELDS = (
    "summa_total_dollar",
    "summa_dollar",
    "summa_naqt",
    "summa_kilik",
    "summa_terminal",
    "summa_transfer",
)


class ExpenseListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source="filial", read_only=True)
    category_detail = ExpenseCategoryListSerializer(source="category", read_only=True)
    employee_detail = UserViewListSerializer(source="employee", read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "filial",
            "filial_detail",
            "category",
            "category_detail",
            "is_salary",
            "employee",
            "employee_detail",
            "summa_total_dollar",
            "summa_dollar",
            "summa_naqt",
            "summa_kilik",
            "summa_terminal",
            "summa_transfer",
            "date",
            "note",
            "is_delete",
        )


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = (
            "id",
            "filial",
            "category",
            "is_salary",
            "employee",
            "summa_total_dollar",
            "summa_dollar",
            "summa_naqt",
            "summa_kilik",
            "summa_terminal",
            "summa_transfer",
            "date",
            "note",
            "is_delete",
        )

    def validate(self, attrs):
        """
        POST va PUT/PATCH uchun 100% aniq hisob-kitob:
        - agar komponentlardan bittasi > 0 bo'lsa: total = sum(components)
        - aks holda: total front yuborgani (yoki 0) bo'lib qoladi
        """
        instance = getattr(self, "instance", None)

        # Update bo'lsa: mavjud qiymatlarni bazaga tayanib olamiz
        def get_current(field: str) -> Decimal:
            if field in attrs:
                return _d(attrs.get(field))
            if instance is not None:
                return _d(getattr(instance, field))
            return Decimal("0")

        summa_dollar = get_current("summa_dollar")
        summa_naqt = get_current("summa_naqt")
        summa_kilik = get_current("summa_kilik")
        summa_terminal = get_current("summa_terminal")
        summa_transfer = get_current("summa_transfer")

        # Manfiy qiymatlarni taqiqlaymiz
        for f_name, v in [
            ("summa_dollar", summa_dollar),
            ("summa_naqt", summa_naqt),
            ("summa_kilik", summa_kilik),
            ("summa_terminal", summa_terminal),
            ("summa_transfer", summa_transfer),
        ]:
            if v < 0:
                raise serializers.ValidationError({f_name: "Manfiy summa bo‘lishi mumkin emas."})

        parts_sum = summa_dollar + summa_naqt + summa_kilik + summa_terminal + summa_transfer

        # totalni ham Decimal + quantize qilib qo'yamiz
        total_in = get_current("summa_total_dollar")
        if total_in < 0:
            raise serializers.ValidationError({"summa_total_dollar": "Manfiy summa bo‘lishi mumkin emas."})

        # Qoidamiz:
        if parts_sum > 0:
            total = parts_sum
        else:
            total = total_in  # front yuborgan bo'lsa shu (yoki 0)

        # Hammasini 2 xonaga keltiramiz
        attrs["summa_dollar"] = _q2(summa_dollar)
        attrs["summa_naqt"] = _q2(summa_naqt)
        attrs["summa_kilik"] = _q2(summa_kilik)
        attrs["summa_terminal"] = _q2(summa_terminal)
        attrs["summa_transfer"] = _q2(summa_transfer)
        attrs["summa_total_dollar"] = _q2(total)

        return attrs