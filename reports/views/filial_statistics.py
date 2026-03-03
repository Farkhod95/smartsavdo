# reports/views.py
from __future__ import annotations

from datetime import date
from calendar import monthrange

from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Filial
from sales.models import OrderHistory, VozvratOrder
from finance.models import DebtRepayment, Expense


def _get_period(year: int, month: int | None) -> tuple[date, date]:
    """
    month berilsa: shu oyning 1-kuni ... oxirgi kuni
    month berilmasa: yil boshidan yil oxirigacha
    """
    if month:
        last_day = monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day)
    return date(year, 1, 1), date(year, 12, 31)


def _sum(_qs, field: str):
    # ✅ logika o‘zgarmaydi: Sum(field) -> NULL bo‘lsa 0
    return Coalesce(
        Sum(field),
        Value(0),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )


class FilialSatisticsReportView(APIView):
    """
    GET /reports/filial-statistics?filial_id=1&year=2026&month=2
    GET /reports/filial-statistics?filial_id=1&year=2026   (month yo'q => butun yil)

    ✅ Qo‘shilganlar (logikaga ta’sir qilmaydi):
    - user filial dostup tekshiruvi (403)
    - Http404 chiqmaydi, tushunarli JSON qaytadi
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ---- params
        filial_id = request.query_params.get("filial_id")
        year = request.query_params.get("year")
        month = request.query_params.get("month")  # optional

        if not filial_id or not year:
            return Response(
                {"detail": "filial_id va year majburiy. month ixtiyoriy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            filial_id_int = int(filial_id)
            year_int = int(year)
            month_int = int(month) if month not in (None, "", "null") else None
            if month_int is not None and not (1 <= month_int <= 12):
                raise ValueError("month 1..12 bo'lishi kerak")
        except Exception:
            return Response(
                {"detail": "Noto'g'ri parametr. filial_id, year (va month) son bo'lishi kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ DOSTUP: userda filial bo‘lmasa 403 (hisob-kitob logikasi o‘zgarmaydi)
        if not request.user.filials.filter(id=filial_id_int).exists():
            return Response(
                {"detail": "Sizda ushbu filial bo‘yicha hisobotni ko‘rish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---- filial exists? (Http404 emas)
        if not Filial.objects.filter(pk=filial_id_int).exists():
            return Response({"detail": "Bunday filial topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        start_date, end_date = _get_period(year_int, month_int)

        # ---- base querysets (logika o‘sha-o‘sha)
        orders_qs = OrderHistory.objects.filter(
            is_delete=False,
            order_filial_id=filial_id_int,
            date__gte=start_date,
            date__lte=end_date,
        )

        vozvrat_qs = VozvratOrder.objects.filter(
            is_delete=False,
            filial_id=filial_id_int,
            date__gte=start_date,
            date__lte=end_date,
        )

        expense_qs = Expense.objects.filter(
            is_delete=False,
            filial_id=filial_id_int,
            date__gte=start_date,
            date__lte=end_date,
        )

        repay_qs = DebtRepayment.objects.filter(
            is_delete=False,
            filial_id=filial_id_int,
            date__gte=start_date,
            date__lte=end_date,
        )

        # ---- aggregates (logika o‘sha-o‘sha)
        orders_agg = orders_qs.aggregate(
            count=Coalesce(Count("id"), Value(0)),
            all_product_summa=_sum(orders_qs, "all_product_summa"),
            profit_usd=_sum(orders_qs, "all_profit_dollar"),
            total_paid_usd=_sum(orders_qs, "summa_total_dollar"),
            total_debt_client=_sum(orders_qs, "total_debt_client"),
            total_debt_today_client=_sum(orders_qs, "total_debt_today_client"),

            paid_dollar=_sum(orders_qs, "summa_dollar"),
            paid_cash=_sum(orders_qs, "summa_naqt"),
            paid_click=_sum(orders_qs, "summa_kilik"),
            paid_terminal=_sum(orders_qs, "summa_terminal"),
            paid_transfer=_sum(orders_qs, "summa_transfer"),

            discount=_sum(orders_qs, "discount_amount"),
            change_usd=_sum(orders_qs, "zdacha_dollar"),
            change_uzs=_sum(orders_qs, "zdacha_som"),
        )

        vozvrat_agg = vozvrat_qs.aggregate(
            count=Coalesce(Count("id"), Value(0)),
            total_refunded_usd=_sum(vozvrat_qs, "summa_total_dollar"),

            refunded_dollar=_sum(vozvrat_qs, "summa_dollar"),
            refunded_cash=_sum(vozvrat_qs, "summa_naqt"),
            refunded_click=_sum(vozvrat_qs, "summa_kilik"),
            refunded_terminal=_sum(vozvrat_qs, "summa_terminal"),
            refunded_transfer=_sum(vozvrat_qs, "summa_transfer"),

            discount=_sum(vozvrat_qs, "discount_amount"),
        )

        expense_agg = expense_qs.aggregate(
            count=Coalesce(Count("id"), Value(0)),
            total_usd=_sum(expense_qs, "summa_total_dollar"),

            dollar=_sum(expense_qs, "summa_dollar"),
            cash=_sum(expense_qs, "summa_naqt"),
            click=_sum(expense_qs, "summa_kilik"),
            terminal=_sum(expense_qs, "summa_terminal"),
            transfer=_sum(expense_qs, "summa_transfer"),
        )

        repay_agg = repay_qs.aggregate(
            count=Coalesce(Count("id"), Value(0)),
            total_paid_usd=_sum(repay_qs, "summa_total_dollar"),

            paid_dollar=_sum(repay_qs, "summa_dollar"),
            paid_cash=_sum(repay_qs, "summa_naqt"),
            paid_click=_sum(repay_qs, "summa_kilik"),
            paid_terminal=_sum(repay_qs, "summa_terminal"),
            paid_transfer=_sum(repay_qs, "summa_transfer"),

            discount=_sum(repay_qs, "discount_amount"),
            change_usd=_sum(repay_qs, "zdacha_dollar"),
            change_uzs=_sum(repay_qs, "zdacha_som"),
        )

        # ---- “net” ko‘rsatkichlar (logika o‘sha-o‘sha)
        net_revenue_usd = (orders_agg["total_paid_usd"] or 0) - (vozvrat_agg["total_refunded_usd"] or 0)
        net_cashflow_usd = (
            (orders_agg["total_paid_usd"] or 0)
            + (repay_agg["total_paid_usd"] or 0)
            - (expense_agg["total_usd"] or 0)
            - (vozvrat_agg["total_refunded_usd"] or 0)
        )

        data = {
            "filters": {
                "filial_id": filial_id_int,
                "year": year_int,
                "month": month_int,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "net_revenue_usd": str(net_revenue_usd),
                "net_cashflow_usd": str(net_cashflow_usd),
            },
            "orders": {
                "count": orders_agg["count"],
                "all_product_summa": str(orders_agg["all_product_summa"]),
                "profit_usd": str(orders_agg["profit_usd"]),
                "total_paid_usd": str(orders_agg["total_paid_usd"]),
                "total_debt_client": str(orders_agg["total_debt_client"]),
                "total_debt_today_client": str(orders_agg["total_debt_today_client"]),
                "payments": {
                    "dollar": str(orders_agg["paid_dollar"]),
                    "cash": str(orders_agg["paid_cash"]),
                    "click": str(orders_agg["paid_click"]),
                    "terminal": str(orders_agg["paid_terminal"]),
                    "transfer": str(orders_agg["paid_transfer"]),
                },
                "discount": str(orders_agg["discount"]),
                "change": {
                    "usd": str(orders_agg["change_usd"]),
                    "uzs": str(orders_agg["change_uzs"]),
                },
            },
            "vozvrat": {
                "count": vozvrat_agg["count"],
                "total_refunded_usd": str(vozvrat_agg["total_refunded_usd"]),
                "payments": {
                    "dollar": str(vozvrat_agg["refunded_dollar"]),
                    "cash": str(vozvrat_agg["refunded_cash"]),
                    "click": str(vozvrat_agg["refunded_click"]),
                    "terminal": str(vozvrat_agg["refunded_terminal"]),
                    "transfer": str(vozvrat_agg["refunded_transfer"]),
                },
                "discount": str(vozvrat_agg["discount"]),
            },
            "expenses": {
                "count": expense_agg["count"],
                "total_usd": str(expense_agg["total_usd"]),
                "payments": {
                    "dollar": str(expense_agg["dollar"]),
                    "cash": str(expense_agg["cash"]),
                    "click": str(expense_agg["click"]),
                    "terminal": str(expense_agg["terminal"]),
                    "transfer": str(expense_agg["transfer"]),
                },
            },
            "debt_repayments": {
                "count": repay_agg["count"],
                "total_paid_usd": str(repay_agg["total_paid_usd"]),
                "payments": {
                    "dollar": str(repay_agg["paid_dollar"]),
                    "cash": str(repay_agg["paid_cash"]),
                    "click": str(repay_agg["paid_click"]),
                    "terminal": str(repay_agg["paid_terminal"]),
                    "transfer": str(repay_agg["paid_transfer"]),
                },
                "discount": str(repay_agg["discount"]),
                "change": {
                    "usd": str(repay_agg["change_usd"]),
                    "uzs": str(repay_agg["change_uzs"]),
                },
            },
        }

        return Response(data, status=status.HTTP_200_OK)