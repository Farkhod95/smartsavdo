# reports/views.py
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Sum, Q, OuterRef, DecimalField, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Filial
from finance.models import DebtRepayment
from sales.models import Client, OrderHistory
from users.models import User


class FilialDashboardReportView(APIView):
    """
    GET /reports/filial-dashboard?filial_id=1&months=12

    ✅ LOGIKA O'ZGARMAYDI:
    - filial_id majburiy
    - filial mavjud bo'lishi shart
    - card_count:
        clients_count = Client(filial, is_delete=False).count()
        karzinka_orders_count = OrderHistory(order_filial, is_delete=False, is_karzinka=False).count()
        users_count = User(order_filial==filial OR filials contains filial).distinct().count()
        debtors_count = Client(filial, is_delete=False, total_debt>1).count()
    - monthly:
        OrderHistory.summa_total_dollar bo‘yicha oy kesimida SUM
        DebtRepayment.summa_total_dollar bo‘yicha oy kesimida SUM
        monthly = months bo‘yicha ketma-ket oylar (start_month..)
    - Dostup (xavfsizlik): user faqat o‘z filialida ko‘radi (403)
    - Http404 qaytmaydi, doim tushunarli JSON xabar qaytadi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filial_id = request.query_params.get("filial_id")
        if not filial_id:
            return Response({"detail": "filial_id majburiy"}, status=status.HTTP_400_BAD_REQUEST)

        # filial_id int bo‘lishi shart
        try:
            filial_id_int = int(filial_id)
        except (TypeError, ValueError):
            return Response({"detail": "filial_id noto'g'ri (int bo'lishi kerak)."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ DOSTUP: userda filial bo‘lmasa 403
        if not request.user.filials.filter(id=filial_id_int).exists():
            return Response(
                {"detail": "Sizda ushbu filial bo‘yicha hisobotni ko‘rish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        # filial mavjudligini tekshiramiz (Http404 emas)
        filial = Filial.objects.filter(pk=filial_id_int).first()
        if not filial:
            return Response({"detail": "Bunday filial topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # Necha oy kesimida (default 12)
        try:
            months = int(request.query_params.get("months", 12))
        except (TypeError, ValueError):
            months = 12
        if months <= 0:
            months = 12

        today = timezone.localdate()
        end_date = today

        # start_month: (months-1) oy oldingi oyning 1-kuni
        start_month = today.replace(day=1)
        for _ in range(months - 1):
            start_month = (start_month - timezone.timedelta(days=1)).replace(day=1)

        # -------------------------
        # CARD COUNT (logika o‘sha-o‘sha)
        # -------------------------
        clients_count = Client.objects.filter(
            filial_id=filial.id,
            is_delete=False
        ).count()

        karzinka_orders_count = OrderHistory.objects.filter(
            order_filial_id=filial.id,
            is_delete=False,
            is_karzinka=False
        ).count()

        users_count = (
            User.objects
            .filter(Q(order_filial_id=filial.id) | Q(filials__id=filial.id))
            .distinct()
            .count()
        )

        # Sizda latest_total_debt_subq bor edi, lekin foydalanilmagan — logikaga ta’sir qilmaslik uchun qoldirdim.
        latest_total_debt_subq = (
            DebtRepayment.objects
            .filter(
                filial_id=filial.id,
                is_delete=False,
                client_id=OuterRef("pk"),
            )
            .annotate(
                sort_date=Coalesce("date", Value(date(1900, 1, 1)))
            )
            .order_by("-sort_date", "-created_time")
            .values("total_debt_client")[:1]
        )

        debtors_count = Client.objects.filter(
            is_delete=False,
            filial_id=filial.id,
            total_debt__gt=1,
        ).count()

        card_count = {
            "clients_count": clients_count,
            "debtors_count": debtors_count,
            "karzinka_orders_count": karzinka_orders_count,
            "users_count": users_count,
        }

        # -------------------------
        # MONTHLY SUMS (logika o‘sha-o‘sha)
        # -------------------------
        order_qs = (
            OrderHistory.objects
            .filter(
                order_filial_id=filial.id,
                is_delete=False,
                date__gte=start_month,
                date__lte=end_date,
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                order_sum_usd=Coalesce(
                    Sum("summa_total_dollar"),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=20, decimal_places=2)),
                )
            )
            .order_by("month")
        )

        order_map = {
            row["month"].isoformat(): row["order_sum_usd"]
            for row in order_qs
            if row["month"]
        }

        debt_qs = (
            DebtRepayment.objects
            .filter(
                filial_id=filial.id,
                is_delete=False,
                date__gte=start_month,
                date__lte=end_date,
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                debt_sum_usd=Coalesce(
                    Sum("summa_total_dollar"),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=20, decimal_places=2)),
                )
            )
            .order_by("month")
        )

        debt_map = {
            row["month"].isoformat(): row["debt_sum_usd"]
            for row in debt_qs
            if row["month"]
        }

        monthly = []
        cur = start_month.replace(day=1)
        for _ in range(months):
            key = cur.isoformat()  # "YYYY-MM-01"
            o = order_map.get(key, Decimal("0.00"))
            d = debt_map.get(key, Decimal("0.00"))

            monthly.append({
                "month": key,
                "order_sum_usd": str(o),
                "debt_sum_usd": str(d),
                "total_sum_usd": str(o + d),
            })

            # keyingi oy (dateutil siz)
            cur = (cur.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)

        return Response(
            {
                "filial_id": filial.id,
                "card_count": card_count,
                "monthly": monthly,
            },
            status=status.HTTP_200_OK,
        )