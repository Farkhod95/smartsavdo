# reports/views.py
from __future__ import annotations

from django.db.models import Max, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from sales.models import Client  # sizda qayerda bo'lsa shuni to'g'rilang
from reports.serializers import DebtorClientSerializer
from restapp.pagination import ResultsSetPagination


class FilialDebtorsReportView(APIView):
    """
    GET /reports/debtors?filial_id=1&page=1&page_size=20

    Response:
      {
        "total_debt_summ": "12345.00",   # shu filtrdagi barcha debtorlar bo‘yicha
        "count": 10,                    # shu filtrdagi umumiy debtorlar soni
        "next": "...",
        "previous": "...",
        "results": [ ... ]              # page bo‘yicha
      }

    ✅ Logika buzilmaydi:
    - Filial bo‘yicha debtorlar: is_delete=False, total_debt>1
    - last_order_date: OrderHistory.date MAX (is_delete=False)
    - sorting: -total_debt, -last_order_date, -id
    - total_debt_summ: hamma debtorlar bo‘yicha umumiy
    - dostub: user faqat o‘z filiali bo‘yicha ko‘ra oladi
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filial_id = request.query_params.get("filial_id")
        if not filial_id:
            return Response(
                {"detail": "filial_id yuborish shart. Masalan: /reports/debtors?filial_id=1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            filial_id_int = int(filial_id)
        except ValueError:
            return Response(
                {"detail": "filial_id noto'g'ri (int bo'lishi kerak)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ DOSTUP: userda shu filial bo‘lmasa 403
        if not request.user.filials.filter(id=filial_id_int).exists():
            return Response(
                {"detail": "Sizda ushbu filial bo‘yicha hisobotni ko‘rish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN,
            )

        base_qs = (
            Client.objects
            .filter(
                is_delete=False,
                filial_id=filial_id_int,
                total_debt__gt=1,
            )
        )

        # Umumiy qarz summasi (shu filtrdagi barcha clientlar bo‘yicha)
        total_debt_summ = base_qs.aggregate(
            s=Coalesce(Sum("total_debt"), 0)
        )["s"] or 0

        # Oxirgi buyurtma sanasi (OrderHistory.date dan MAX)
        qs = (
            base_qs
            .annotate(
                last_order_date=Max(
                    "order_histories__date",
                    filter=Q(order_histories__is_delete=False),
                )
            )
            .values(
                "id",
                "full_name",
                "phone_number",
                "total_debt",
                "keshbek",
                "last_order_date",
            )
            .order_by("-total_debt", "-last_order_date", "-id")
        )

        # ✅ Pagination (server qotib qolmasin)
        paginator = ResultsSetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        serializer = DebtorClientSerializer(page, many=True)

        # paginator.get_paginated_response() formatiga moslab:
        paginated = paginator.get_paginated_response(serializer.data).data

        # ✅ total_debt_summ va count (umumiy debtorlar soni) ni ham qo‘shib yuboramiz
        # paginator ichidagi count ham aynan umumiy count bo‘ladi
        paginated["total_debt_summ"] = str(total_debt_summ)

        return Response(paginated, status=status.HTTP_200_OK)