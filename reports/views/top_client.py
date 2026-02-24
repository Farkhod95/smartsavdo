# reports/views.py
from datetime import datetime
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from sales.models import OrderHistory  # sizda qayerda bo'lsa shuni to'g'rilang
from reports.serializers import TopClientItemSerializer


def parse_date_yyyy_mm_dd(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def d0():
    return Decimal("0.00")


class FilialTopClientReportView(APIView):
    """
    GET /reports/top-client?filial_id=1&date_from=2026-02-01&date_to=2026-02-24

    Natija: top clientlar order_count bo'yicha desc.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filial_id = request.query_params.get("filial_id")
        date_from_raw = request.query_params.get("date_from")
        date_to_raw = request.query_params.get("date_to")

        if not filial_id:
            return Response(
                {"detail": "filial_id yuborish shart. Masalan: ?filial_id=1&date_from=2026-02-01&date_to=2026-02-24"},
                status=status.HTTP_400_BAD_REQUEST
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
                status=status.HTTP_400_BAD_REQUEST
            )

        if date_from > date_to:
            return Response({"detail": "date_from date_to dan katta bo'lmasligi kerak."}, status=status.HTTP_400_BAD_REQUEST)

        # OrderHistory -> client bo'yicha group
        qs = (
            OrderHistory.objects
            .filter(
                is_delete=False,
                order_filial_id=filial_id,
                date__gte=date_from,
                date__lte=date_to,
                client__isnull=False,
            )
            .values("client_id", "client__full_name")
            .annotate(
                order_count=Count("id"),
                sum_summa_total_dollar=Coalesce(Sum("summa_total_dollar"), d0()),
                sum_all_product_summa=Coalesce(Sum("all_product_summa"), d0()),
                sum_all_profit_dollar=Coalesce(Sum("all_profit_dollar"), d0()),
            )
            .order_by("-order_count", "-sum_summa_total_dollar", "-client_id")
        )

        items = [
            {
                "client_id": row["client_id"],
                "client_full_name": row["client__full_name"],
                "order_count": row["order_count"],
                "sum_summa_total_dollar": row["sum_summa_total_dollar"],
                "sum_all_product_summa": row["sum_all_product_summa"],
                "sum_all_profit_dollar": row["sum_all_profit_dollar"],
            }
            for row in qs
        ]

        serializer = TopClientItemSerializer(items, many=True)

        return Response(
            {
                "filters": {
                    "filial_id": filial_id,
                    "date_from": str(date_from),
                    "date_to": str(date_to),
                },
                "count": len(serializer.data),
                "items": serializer.data,
            },
            status=status.HTTP_200_OK
        )