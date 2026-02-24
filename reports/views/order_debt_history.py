# reports/views.py
from datetime import datetime
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from sales.models import OrderHistory, Client  # to'g'rilang
from finance.models import DebtRepayment, Expense  # to'g'rilang
# ExpenseCategory kerak bo'lsa modeldan o'zi join bo'ladi

from reports.serializers import (
    OrderHistoryItemSerializer,
    DebtRepaymentItemSerializer,
    ExpenseItemSerializer,
)


def parse_date_yyyy_mm_dd(value: str):
    """
    '2026-02-01' -> date
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def d0():
    return Decimal("0.00")


class FiliaOrderDebtHistoryReportView(APIView):
    """
    GET /reports/order-debt-history?filial_id=1&date_from=2026-02-01&date_to=2026-02-24
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filial_id = request.query_params.get("filial_id")
        date_from_raw = request.query_params.get("date_from")
        date_to_raw = request.query_params.get("date_to")

        if not filial_id:
            return Response(
                {"detail": "filial_id yuborish shart. Masalan: ?filial_id=1&date_from=2026-02-01&date_to=2026-02-24"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            filial_id = int(filial_id)
        except ValueError:
            return Response({"detail": "filial_id noto'g'ri (int bo'lishi kerak)."}, status=status.HTTP_400_BAD_REQUEST)

        date_from = parse_date_yyyy_mm_dd(date_from_raw)
        date_to = parse_date_yyyy_mm_dd(date_to_raw)

        if not date_from or not date_to:
            return Response(
                {"detail": "date_from va date_to YYYY-MM-DD formatda bo'lishi kerak. Masalan: 2026-02-01"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if date_from > date_to:
            return Response({"detail": "date_from date_to dan katta bo'lmasligi kerak."}, status=status.HTTP_400_BAD_REQUEST)

        # =============== 1) OrderHistory ===============
        orders_qs = (
            OrderHistory.objects
            .filter(
                is_delete=False,
                order_filial_id=filial_id,
                date__gte=date_from,
                date__lte=date_to,
            )
            .select_related("client")
            .order_by("-date", "-id")
        )

        orders_totals = orders_qs.aggregate(
            all_product_summa=Coalesce(Sum("all_product_summa"), d0()),
            summa_total_dollar=Coalesce(Sum("summa_total_dollar"), d0()),
            summa_dollar=Coalesce(Sum("summa_dollar"), d0()),
            summa_naqt=Coalesce(Sum("summa_naqt"), d0()),
            summa_kilik=Coalesce(Sum("summa_kilik"), d0()),
            summa_terminal=Coalesce(Sum("summa_terminal"), d0()),
            summa_transfer=Coalesce(Sum("summa_transfer"), d0()),
            discount_amount=Coalesce(Sum("discount_amount"), d0()),
            zdacha_dollar=Coalesce(Sum("zdacha_dollar"), d0()),
            zdacha_som=Coalesce(Sum("zdacha_som"), d0()),
        )

        orders_items = [
            {
                "client_full_name": (o.client.full_name if o.client else None),
                "date": o.date,
                "summa_total_dollar": o.summa_total_dollar,
                "all_product_summa": o.all_product_summa,
            }
            for o in orders_qs
        ]

        # serializer optional (data structure tekshirish uchun)
        orders_items_ser = OrderHistoryItemSerializer(orders_items, many=True).data

        # =============== 2) DebtRepayment ===============
        repayments_qs = (
            DebtRepayment.objects
            .filter(
                is_delete=False,
                filial_id=filial_id,
                date__gte=date_from,
                date__lte=date_to,
            )
            .select_related("client")
            .order_by("-date", "-id")
        )

        repayments_totals = repayments_qs.aggregate(
            summa_total_dollar=Coalesce(Sum("summa_total_dollar"), d0()),
            summa_dollar=Coalesce(Sum("summa_dollar"), d0()),
            summa_naqt=Coalesce(Sum("summa_naqt"), d0()),
            summa_kilik=Coalesce(Sum("summa_kilik"), d0()),
            summa_terminal=Coalesce(Sum("summa_terminal"), d0()),
            summa_transfer=Coalesce(Sum("summa_transfer"), d0()),
            discount_amount=Coalesce(Sum("discount_amount"), d0()),
            zdacha_dollar=Coalesce(Sum("zdacha_dollar"), d0()),
            zdacha_som=Coalesce(Sum("zdacha_som"), d0()),
        )

        repayments_items = [
            {
                "client_full_name": (r.client.full_name if r.client else None),
                "date": r.date,
                "summa_total_dollar": r.summa_total_dollar,
            }
            for r in repayments_qs
        ]
        repayments_items_ser = DebtRepaymentItemSerializer(repayments_items, many=True).data

        # =============== 3) Expense ===============
        expenses_qs = (
            Expense.objects
            .filter(
                is_delete=False,
                filial_id=filial_id,
                date__gte=date_from,
                date__lte=date_to,
            )
            .select_related("category")
            .order_by("-date", "-id")
        )

        expenses_totals = expenses_qs.aggregate(
            summa_total_dollar=Coalesce(Sum("summa_total_dollar"), d0()),
            summa_dollar=Coalesce(Sum("summa_dollar"), d0()),
            summa_naqt=Coalesce(Sum("summa_naqt"), d0()),
            summa_kilik=Coalesce(Sum("summa_kilik"), d0()),
            summa_terminal=Coalesce(Sum("summa_terminal"), d0()),
            summa_transfer=Coalesce(Sum("summa_transfer"), d0()),
        )

        expenses_items = [
            {
                "date": e.date,
                "category_name": (e.category.name if e.category else None),
                "summa_total_dollar": e.summa_total_dollar,
                "summa_dollar": e.summa_dollar,
                "summa_naqt": e.summa_naqt,
                "summa_kilik": e.summa_kilik,
                "summa_terminal": e.summa_terminal,
                "summa_transfer": e.summa_transfer,
            }
            for e in expenses_qs
        ]
        expenses_items_ser = ExpenseItemSerializer(expenses_items, many=True).data

        # =============== Response ===============
        return Response(
            {
                "filters": {
                    "filial_id": filial_id,
                    "date_from": str(date_from),
                    "date_to": str(date_to),
                },

                "orders": {
                    "total": {
                        "all_product_summa": str(orders_totals["all_product_summa"]),
                        "summa_total_dollar": str(orders_totals["summa_total_dollar"]),
                        "summa_dollar": str(orders_totals["summa_dollar"]),
                        "summa_naqt": str(orders_totals["summa_naqt"]),
                        "summa_kilik": str(orders_totals["summa_kilik"]),
                        "summa_terminal": str(orders_totals["summa_terminal"]),
                        "summa_transfer": str(orders_totals["summa_transfer"]),
                        "discount_amount": str(orders_totals["discount_amount"]),
                        "zdacha_dollar": str(orders_totals["zdacha_dollar"]),
                        "zdacha_som": str(orders_totals["zdacha_som"]),
                    },
                    "count": len(orders_items_ser),
                    "items": orders_items_ser,
                },

                "repayments": {
                    "total": {
                        "summa_total_dollar": str(repayments_totals["summa_total_dollar"]),
                        "summa_dollar": str(repayments_totals["summa_dollar"]),
                        "summa_naqt": str(repayments_totals["summa_naqt"]),
                        "summa_kilik": str(repayments_totals["summa_kilik"]),
                        "summa_terminal": str(repayments_totals["summa_terminal"]),
                        "summa_transfer": str(repayments_totals["summa_transfer"]),
                        "discount_amount": str(repayments_totals["discount_amount"]),
                        "zdacha_dollar": str(repayments_totals["zdacha_dollar"]),
                        "zdacha_som": str(repayments_totals["zdacha_som"]),
                    },
                    "count": len(repayments_items_ser),
                    "items": repayments_items_ser,
                },

                "expenses": {
                    "total": {
                        "summa_total_dollar": str(expenses_totals["summa_total_dollar"]),
                        "summa_dollar": str(expenses_totals["summa_dollar"]),
                        "summa_naqt": str(expenses_totals["summa_naqt"]),
                        "summa_kilik": str(expenses_totals["summa_kilik"]),
                        "summa_terminal": str(expenses_totals["summa_terminal"]),
                        "summa_transfer": str(expenses_totals["summa_transfer"]),
                    },
                    "count": len(expenses_items_ser),
                    "items": expenses_items_ser,
                },
            },
            status=status.HTTP_200_OK,
        )