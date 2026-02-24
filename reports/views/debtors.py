# reports/views.py
from django.db.models import Max, Q, Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from sales.models import Client  # sizda qayerda bo'lsa shuni to'g'rilang
from reports.serializers import DebtorClientSerializer


class FilialDebtorsReportView(APIView):
    """
    GET /reports/debtors?filial_id=1

    Response:
      {
        "total_debt_summ": "12345.00",
        "count": 10,
        "results": [ ... ]
      }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filial_id = request.query_params.get("filial_id")
        if not filial_id:
            return Response(
                {"detail": "filial_id yuborish shart. Masalan: /reports/debtors?filial_id=1"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            filial_id_int = int(filial_id)
        except ValueError:
            return Response({"detail": "filial_id noto'g'ri (int bo'lishi kerak)."}, status=status.HTTP_400_BAD_REQUEST)

        base_qs = (
            Client.objects
            .filter(
                is_delete=False,
                filial_id=filial_id_int,
                total_debt__gt=1
            )
        )

        # Umumiy qarz summasi (shu filtrdagi clientlar bo'yicha)
        total_debt_summ = base_qs.aggregate(s=Sum("total_debt"))["s"] or 0

        # Oxirgi buyurtma sanasi (OrderHistory.date dan MAX)
        qs = (
            base_qs
            .annotate(
                last_order_date=Max(
                    "order_histories__date",
                    filter=Q(order_histories__is_delete=False)
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

        data = list(qs)
        serializer = DebtorClientSerializer(data, many=True)

        return Response({
            "total_debt_summ": str(total_debt_summ),
            "count": len(serializer.data),
            "results": serializer.data
        }, status=status.HTTP_200_OK)