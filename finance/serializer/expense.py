# finance/serializer/expense.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from rest_framework import serializers

from finance.models import Expense

Q = Decimal("0.01")  # 2 ta kasr (tiyin/sent) aniqligi


def _d(val) -> Decimal:
    """
    Safe Decimal convert:
    None / "" -> 0
    """
    if val is None or val == "":
        return Decimal("0")
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _q2(val: Decimal) -> Decimal:
    return _d(val).quantize(Q, rounding=ROUND_HALF_UP)


MONEY_PART_FIELDS = (
    "summa_dollar",
    "summa_naqt",
    "summa_kilik",
    "summa_terminal",
    "summa_transfer",
)


class ExpenseSerializer(serializers.ModelSerializer):
    # totalni frontdan qabul qilmaymiz (backend o'zi hisoblaydi)
    summa_total_dollar = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )

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
        POST/PUT uchun:
        - barcha summalarni Decimal(0.01) ga keltiradi
        - minus bo'lmasligini tekshiradi
        - summa_total_dollar ni backendda aniq hisoblaydi
        """
        # Instance bo'lsa (PUT/PATCH) — eski qiymatlarni ham hisobga olamiz
        data = {}
        inst = getattr(self, "instance", None)

        # 1) money fieldlarni normalizatsiya qilamiz
        for f in MONEY_PART_FIELDS:
            incoming = attrs.get(f, None)
            if incoming is None and inst is not None:
                incoming = getattr(inst, f)

            val = _q2(incoming)
            if val < 0:
                raise serializers.ValidationError({f: "Manfiy summa bo‘lishi mumkin emas."})

            data[f] = val

        # 2) totalni backendda aniq hisoblaymiz
        total = sum((data[f] for f in MONEY_PART_FIELDS), Decimal("0"))
        attrs["summa_total_dollar"] = _q2(total)

        # 3) attrs ichiga normalizatsiya qilingan qiymatlarni qaytarib qo'yamiz
        for f, v in data.items():
            attrs[f] = v

        return attrs

    def create(self, validated_data):
        # summa_total_dollar validate() da aniq hisoblangan bo'ladi
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # summa_total_dollar validate() da aniq qayta hisoblangan bo'ladi
        return super().update(instance, validated_data)