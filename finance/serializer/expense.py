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
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete')


Q = Decimal("0.01")

MONEY_PART_FIELDS = (
    "summa_dollar",
    "summa_naqt",
    "summa_kilik",
    "summa_terminal",
    "summa_transfer",
)

def fast_decimal(val, field_name: str) -> Decimal:
    """
    Juda tez parse:
    - None / "" => 0.00
    - "1200" / 1200 / "1200.50" => ok
    Noto'g'ri format => ValidationError
    """
    if val is None or val == "":
        return Decimal("0.00")
    try:
        d = Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        raise serializers.ValidationError({field_name: "Summa formati noto‘g‘ri."})
    return d.quantize(Q, rounding=ROUND_HALF_UP)

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

    def _calc_total(self, data: dict, instance=None) -> dict:
        # 1) faqat part fieldlar parse qilinadi (tez)
        parts = {}
        for f in MONEY_PART_FIELDS:
            if f in data:
                parts[f] = fast_decimal(data.get(f), f)
                if parts[f] < 0:
                    raise serializers.ValidationError({f: "Manfiy summa bo‘lishi mumkin emas."})
            elif instance is not None:
                parts[f] = instance.__dict__.get(f) or Decimal("0.00")
            else:
                parts[f] = Decimal("0.00")

        # 2) totalni backendda aniq hisoblaymiz
        total = sum(parts.values(), Decimal("0.00")).quantize(Q, rounding=ROUND_HALF_UP)

        # 3) data ga yozib qo'yamiz
        for f, v in parts.items():
            if f in data:   # faqat kelgan fieldlarni update qilamiz
                data[f] = v
        data["summa_total_dollar"] = total
        return data

    def create(self, validated_data):
        validated_data = self._calc_total(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._calc_total(validated_data, instance=instance)
        return super().update(instance, validated_data)