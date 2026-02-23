# reports/views.py
from datetime import date
from decimal import Decimal

from django.db.models import Sum, Count, Q, OuterRef, Subquery, DecimalField, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Filial  # sizda qayerda bo'lsa shuni yozing
from finance.models import DebtRepayment
from sales.models import Client, OrderHistory
from users.models import User  # sizda User modeli qayerda bo'lsa shuni yozing


class FilialDashboardReportView(APIView):
    """
    GET reports/filial-dashboard/?filial_id=1
    card_count:
        clients_count — shu filialga tegishli Clientlar soni
        debtors_count — qarzdor mijozlar soni (oxirgi holatda total_debt_client > 0)
        karzinka_orders_count — OrderHistory.is_karzinka = true bo‘lgan orderlar soni
        users_count — shu filialga ulangan userlar soni (order_filial yoki filials M2M)
    monthly[]:
        month — oy boshi (YYYY-MM-01) formatida
        order_sum_usd — OrderHistory.summa_total_dollar oy bo‘yicha yig‘indisi
        debt_sum_usd — DebtRepayment.summa_total_dollar oy bo‘yicha yig‘indisi
        total_sum_usd — order_sum_usd + debt_sum_usd

    Response:
    {
      "filial_id": 3,
      "card_count": {
        "clients_count": 120,
        "debtors_count": 18,
        "karzinka_orders_count": 44,
        "users_count": 7
      },
      "monthly": [
        {
          "month": "2025-03-01",
          "order_sum_usd": "1200.00",
          "debt_sum_usd": "300.00",
          "total_sum_usd": "1500.00"
        },
        {
          "month": "2025-04-01",
          "order_sum_usd": "0.00",
          "debt_sum_usd": "50.00",
          "total_sum_usd": "50.00"
        }
      ]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filial_id = request.query_params.get("filial_id")
        if not filial_id:
            return Response({"detail": "filial_id majburiy"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            filial = Filial.objects.get(pk=filial_id)
        except Filial.DoesNotExist:
            return Response({"detail": "Bunday filial topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # Necha oy kesimida qaytarish (default 12)
        months = int(request.query_params.get("months", 12))
        if months <= 0:
            months = 12

        today = timezone.localdate()
        # Oy kesimi bo'yicha range: (months-1) oy oldin -> hozirgi oy oxiri
        start_month = (today.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)  # o'tgan oy boshi
        # yuqoridagi oddiy emas, shuning uchun aniqroq:
        # start_month = (today.replace(day=1) - relativedelta(months=months-1))  # agar dateutil bo'lsa
        # dateutil ishlatmaslik uchun:
        # months ni loop bilan orqaga qaytaramiz:
        start_month = today.replace(day=1)
        for _ in range(months - 1):
            start_month = (start_month - timezone.timedelta(days=1)).replace(day=1)

        end_date = today  # inclusive

        # -------------------------
        # CARD COUNT
        # -------------------------

        # 1) Clients count (filial bo'yicha)
        clients_count = Client.objects.filter(
            filial_id=filial.id,
            is_delete=False
        ).count()

        # 2) Karzinka count
        karzinka_orders_count = OrderHistory.objects.filter(
            order_filial_id=filial.id,
            is_delete=False,
            is_karzinka=False
        ).count()

        # 3) Users count (order_filial yoki filials m2m)
        users_count = User.objects.filter(
            Q(order_filial_id=filial.id) | Q(filials__id=filial.id)
        ).distinct().count()

        # 4) Debtors count (DebtRepayment oxirgi holat bo'yicha total_debt_client > 0)
        # Oxirgi repaymentni aniqlash: date bo'lsa date, bo'lmasa created_time.
        # Sizda BaseModel'da created_time bor (ko'p joyda ishlatilgan), deb hisoblayman.
        latest_total_debt_subq = DebtRepayment.objects.filter(
            filial_id=filial.id,
            is_delete=False,
            client_id=OuterRef("pk"),
        ).order_by(
            Coalesce("date", Value(date(1900, 1, 1))),  # date null bo'lsa eng past
            "created_time"
        ).values("total_debt_client")[:1]

        # MUHIM: order_by teskari bo'lishi kerak (eng oxirgi)
        latest_total_debt_subq = DebtRepayment.objects.filter(
            filial_id=filial.id,
            is_delete=False,
            client_id=OuterRef("pk"),
        ).order_by(
            Coalesce("date", Value(date(1900, 1, 1))).desc(),
            "-created_time"
        ).values("total_debt_client")[:1]

        debtors_count = Client.objects.filter(
            filial_id=filial.id,
            is_delete=False
        ).annotate(
            latest_total_debt=Coalesce(
                Subquery(latest_total_debt_subq, output_field=DecimalField(max_digits=20, decimal_places=2)),
                Value(Decimal("0.00"))
            )
        ).filter(latest_total_debt__gt=0).count()

        card_count = {
            "clients_count": clients_count,
            "debtors_count": debtors_count,
            "karzinka_orders_count": karzinka_orders_count,
            "users_count": users_count,
        }

        # -------------------------
        # MONTHLY SUMS
        # -------------------------

        # OrderHistory monthly
        order_qs = OrderHistory.objects.filter(
            order_filial_id=filial.id,
            is_delete=False,
            date__gte=start_month,
            date__lte=end_date,
        ).annotate(
            month=TruncMonth("date")
        ).values("month").annotate(
            order_sum_usd=Coalesce(Sum("summa_total_dollar"), Value(Decimal("0.00")))
        ).order_by("month")

        order_map = {row["month"].date().isoformat(): row["order_sum_usd"] for row in order_qs if row["month"]}

        # DebtRepayment monthly
        debt_qs = DebtRepayment.objects.filter(
            filial_id=filial.id,
            is_delete=False,
            date__gte=start_month,
            date__lte=end_date,
        ).annotate(
            month=TruncMonth("date")
        ).values("month").annotate(
            debt_sum_usd=Coalesce(Sum("summa_total_dollar"), Value(Decimal("0.00")))
        ).order_by("month")

        debt_map = {row["month"].date().isoformat(): row["debt_sum_usd"] for row in debt_qs if row["month"]}

        # To'liq oylar ro'yxatini to'ldirib chiqamiz (bo'sh oylar ham 0 bo'lib kelsin)
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

            # keyingi oyga o'tish (dateutil ishlatmasdan)
            # 1) shu oyning oxirgi kuniga o'tib, +1 kun qilib keyingi oy boshiga chiqamiz
            next_month = (cur.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
            cur = next_month

        return Response({
            "filial_id": filial.id,
            "card_count": card_count,
            "monthly": monthly
        }, status=status.HTTP_200_OK)