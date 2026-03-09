from collections import OrderedDict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from finance.models import DebtRepayment
from reports.serializers import OrdersAndDebtsReportGroupSerializer
from restapp.pagination import ResultsSetPagination
from sales.models import OrderHistory


class OrdersAndDebtsReportView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def _d(self, value) -> Decimal:
        if value in (None, "", "null"):
            return Decimal("0")
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal("0")

    def _format_money(self, value) -> str:
        return f"{self._d(value):.2f}"

    def _parse_int_optional(self, value, field_name):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError({field_name: f"{field_name} noto‘g‘ri formatda."})

    def _parse_date_optional(self, value, field_name):
        if not value:
            return None

        parsed = parse_date(value)
        if parsed:
            return parsed

        try:
            return datetime.strptime(value, "%d.%m.%Y").date()
        except Exception:
            raise ValidationError({
                field_name: f"{field_name} formati noto‘g‘ri. Masalan: 2026-03-08 yoki 08.03.2026"
            })

    def _aware_day_start(self, date_value):
        dt = datetime.combine(date_value, time.min)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def _aware_next_day_start(self, date_value):
        dt = datetime.combine(date_value + timedelta(days=1), time.min)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def _get_user_filial_ids(self, user):
        return list(user.filials.values_list("id", flat=True))

    def get(self, request, *args, **kwargs):
        user = request.user

        filial_id = self._parse_int_optional(request.query_params.get("filial_id"), "filial_id")
        client_id = self._parse_int_optional(request.query_params.get("client_id"), "client_id")
        date_from = self._parse_date_optional(request.query_params.get("date_from"), "date_from")
        date_to = self._parse_date_optional(request.query_params.get("date_to"), "date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError({
                "date_to": "date_to date_from dan kichik bo‘lishi mumkin emas."
            })

        user_filial_ids = self._get_user_filial_ids(user)

        if not user_filial_ids:
            paginator = ResultsSetPagination()
            paginator.set_filter({
                "filial_id": filial_id,
                "client_id": client_id,
                "date_from": request.query_params.get("date_from"),
                "date_to": request.query_params.get("date_to"),
            })
            page = paginator.paginate_queryset([], request, view=self)
            return paginator.get_paginated_response(page)

        allowed_filial_ids = user_filial_ids
        if filial_id is not None:
            if filial_id not in user_filial_ids:
                raise ValidationError({"filial_id": "Sizda ushbu filialga dostup yo‘q."})
            allowed_filial_ids = [filial_id]

        order_qs = (
            OrderHistory.objects
            .filter(
                is_delete=False,
                is_karzinka=False,
                order_filial_id__in=allowed_filial_ids,
                created_time__isnull=False,
            )
            .select_related("client", "employee", "order_filial")
        )

        debt_qs = (
            DebtRepayment.objects
            .filter(
                is_delete=False,
                filial_id__in=allowed_filial_ids,
                created_time__isnull=False,
            )
            .select_related("client", "employee", "filial")
        )

        if client_id is not None:
            order_qs = order_qs.filter(client_id=client_id)
            debt_qs = debt_qs.filter(client_id=client_id)

        if date_from:
            start_dt = self._aware_day_start(date_from)
            order_qs = order_qs.filter(created_time__gte=start_dt)
            debt_qs = debt_qs.filter(created_time__gte=start_dt)

        if date_to:
            end_dt = self._aware_next_day_start(date_to)
            order_qs = order_qs.filter(created_time__lt=end_dt)
            debt_qs = debt_qs.filter(created_time__lt=end_dt)

        order_rows = []
        for obj in order_qs:
            created_dt = obj.created_time
            created_date = timezone.localtime(created_dt).date() if created_dt else None

            order_rows.append({
                "type": "order",
                "date": created_date,
                "datetime": created_dt,
                "object_id": obj.id,
                "client_id": obj.client_id,
                "client_name": getattr(obj.client, "full_name", None),
                "employee_id": obj.employee_id,
                "employee_name": getattr(obj.employee, "full_name", None) or getattr(obj.employee, "username", None),

                "all_product_summa": self._d(obj.all_product_summa),
                "all_profit_dollar": self._d(obj.all_profit_dollar),
                "total_debt_client": self._d(obj.total_debt_client),

                "summa_total_dollar": self._d(obj.summa_total_dollar),
                "summa_dollar": self._d(obj.summa_dollar),
                "summa_naqt": self._d(obj.summa_naqt),
                "summa_kilik": self._d(obj.summa_kilik),
                "summa_terminal": self._d(obj.summa_terminal),
                "summa_transfer": self._d(obj.summa_transfer),
                "discount_amount": self._d(obj.discount_amount),
                "zdacha_dollar": self._d(obj.zdacha_dollar),

                "vaqti": timezone.localtime(created_dt).strftime("%d.%m.%Y %H:%M") if created_dt else None,
                "holati": "Buyurtma qilingan",
            })

        debt_rows = []
        for obj in debt_qs:
            created_dt = obj.created_time
            created_date = timezone.localtime(created_dt).date() if created_dt else None

            debt_rows.append({
                "type": "debt",
                "date": created_date,
                "datetime": created_dt,
                "object_id": obj.id,
                "client_id": obj.client_id,
                "client_name": getattr(obj.client, "full_name", None),
                "employee_id": obj.employee_id,
                "employee_name": getattr(obj.employee, "full_name", None) or getattr(obj.employee, "username", None),

                "all_product_summa": Decimal("0"),
                "all_profit_dollar": Decimal("0"),
                "total_debt_client": self._d(obj.total_debt_client),

                "summa_total_dollar": self._d(obj.summa_total_dollar),
                "summa_dollar": self._d(obj.summa_dollar),
                "summa_naqt": self._d(obj.summa_naqt),
                "summa_kilik": self._d(obj.summa_kilik),
                "summa_terminal": self._d(obj.summa_terminal),
                "summa_transfer": self._d(obj.summa_transfer),
                "discount_amount": self._d(obj.discount_amount),
                "zdacha_dollar": self._d(obj.zdacha_dollar),

                "vaqti": timezone.localtime(created_dt).strftime("%d.%m.%Y %H:%M") if created_dt else None,
                "holati": "Qarz to‘lagan",
            })

        all_rows = order_rows + debt_rows

        all_rows.sort(
            key=lambda x: (
                x["date"] or datetime.min.date(),
                x["datetime"] or datetime.min.replace(tzinfo=timezone.get_current_timezone()),
                x["object_id"],
            ),
            reverse=True
        )

        grouped = OrderedDict()

        for row in all_rows:
            row_date = row["date"]
            if row_date is None:
                continue

            date_key = row_date.isoformat()

            if date_key not in grouped:
                grouped[date_key] = {
                    "date": row_date,
                    "date_label": row_date.strftime("%d.%m.%Y"),
                    "count": 0,
                    "totals": {
                        "totalproduct_summa": Decimal("0"),
                        "totalprofit": Decimal("0"),
                        "total_all_qarz": Decimal("0"),
                        "orders": {
                            "all_profit_dollar": Decimal("0"),
                            "summa_total_dollar": Decimal("0"),
                            "summa_dollar": Decimal("0"),
                            "summa_naqt": Decimal("0"),
                            "summa_kilik": Decimal("0"),
                            "summa_terminal": Decimal("0"),
                            "summa_transfer": Decimal("0"),
                            "discount_amount": Decimal("0"),
                            "zdacha_dollar": Decimal("0"),
                        },
                        "debts": {
                            "summa_total_dollar": Decimal("0"),
                            "summa_dollar": Decimal("0"),
                            "summa_naqt": Decimal("0"),
                            "summa_kilik": Decimal("0"),
                            "summa_terminal": Decimal("0"),
                            "summa_transfer": Decimal("0"),
                            "discount_amount": Decimal("0"),
                            "zdacha_dollar": Decimal("0"),
                        }
                    },
                    "items": []
                }

            group = grouped[date_key]
            group["count"] += 1
            row_number = group["count"]

            group["items"].append({
                "row_number": row_number,
                "type": row["type"],
                "object_id": row["object_id"],
                "client_id": row["client_id"],
                "client_name": row["client_name"],
                "employee_id": row["employee_id"],
                "employee_name": row["employee_name"],

                "all_product_summa": row["all_product_summa"],
                "all_profit_dollar": row["all_profit_dollar"],
                "total_debt_client": row["total_debt_client"],

                "summa_total_dollar": row["summa_total_dollar"],
                "summa_dollar": row["summa_dollar"],
                "summa_naqt": row["summa_naqt"],
                "summa_kilik": row["summa_kilik"],
                "summa_terminal": row["summa_terminal"],
                "summa_transfer": row["summa_transfer"],
                "discount_amount": row["discount_amount"],
                "zdacha_dollar": row["zdacha_dollar"],

                "vaqti": row["vaqti"],
                "holati": row["holati"],
                "datetime": row["datetime"],
            })

            group["totals"]["total_all_qarz"] += row["total_debt_client"]

            if row["type"] == "order":
                group["totals"]["totalproduct_summa"] += row["all_product_summa"]
                group["totals"]["totalprofit"] += row["all_profit_dollar"]

                group["totals"]["orders"]["all_profit_dollar"] += row["all_profit_dollar"]
                group["totals"]["orders"]["summa_total_dollar"] += row["summa_total_dollar"]
                group["totals"]["orders"]["summa_dollar"] += row["summa_dollar"]
                group["totals"]["orders"]["summa_naqt"] += row["summa_naqt"]
                group["totals"]["orders"]["summa_kilik"] += row["summa_kilik"]
                group["totals"]["orders"]["summa_terminal"] += row["summa_terminal"]
                group["totals"]["orders"]["summa_transfer"] += row["summa_transfer"]
                group["totals"]["orders"]["discount_amount"] += row["discount_amount"]
                group["totals"]["orders"]["zdacha_dollar"] += row["zdacha_dollar"]

            elif row["type"] == "debt":
                group["totals"]["debts"]["summa_total_dollar"] += row["summa_total_dollar"]
                group["totals"]["debts"]["summa_dollar"] += row["summa_dollar"]
                group["totals"]["debts"]["summa_naqt"] += row["summa_naqt"]
                group["totals"]["debts"]["summa_kilik"] += row["summa_kilik"]
                group["totals"]["debts"]["summa_terminal"] += row["summa_terminal"]
                group["totals"]["debts"]["summa_transfer"] += row["summa_transfer"]
                group["totals"]["debts"]["discount_amount"] += row["discount_amount"]
                group["totals"]["debts"]["zdacha_dollar"] += row["zdacha_dollar"]

        grouped_list = []
        for group in grouped.values():
            grouped_list.append({
                "date": group["date"],
                "date_label": group["date_label"],
                "count": group["count"],
                "totals": {
                    "totalproduct_summa": self._format_money(group["totals"]["totalproduct_summa"]),
                    "totalprofit": self._format_money(group["totals"]["totalprofit"]),
                    "total_all_qarz": self._format_money(group["totals"]["total_all_qarz"]),
                    "orders": {
                        "all_profit_dollar": self._format_money(group["totals"]["orders"]["all_profit_dollar"]),
                        "summa_total_dollar": self._format_money(group["totals"]["orders"]["summa_total_dollar"]),
                        "summa_dollar": self._format_money(group["totals"]["orders"]["summa_dollar"]),
                        "summa_naqt": self._format_money(group["totals"]["orders"]["summa_naqt"]),
                        "summa_kilik": self._format_money(group["totals"]["orders"]["summa_kilik"]),
                        "summa_terminal": self._format_money(group["totals"]["orders"]["summa_terminal"]),
                        "summa_transfer": self._format_money(group["totals"]["orders"]["summa_transfer"]),
                        "discount_amount": self._format_money(group["totals"]["orders"]["discount_amount"]),
                        "zdacha_dollar": self._format_money(group["totals"]["orders"]["zdacha_dollar"]),
                    },
                    "debts": {
                        "summa_total_dollar": self._format_money(group["totals"]["debts"]["summa_total_dollar"]),
                        "summa_dollar": self._format_money(group["totals"]["debts"]["summa_dollar"]),
                        "summa_naqt": self._format_money(group["totals"]["debts"]["summa_naqt"]),
                        "summa_kilik": self._format_money(group["totals"]["debts"]["summa_kilik"]),
                        "summa_terminal": self._format_money(group["totals"]["debts"]["summa_terminal"]),
                        "summa_transfer": self._format_money(group["totals"]["debts"]["summa_transfer"]),
                        "discount_amount": self._format_money(group["totals"]["debts"]["discount_amount"]),
                        "zdacha_dollar": self._format_money(group["totals"]["debts"]["zdacha_dollar"]),
                    }
                },
                "items": [
                    {
                        **item,
                        "all_product_summa": self._format_money(item["all_product_summa"]),
                        "all_profit_dollar": self._format_money(item["all_profit_dollar"]),
                        "total_debt_client": self._format_money(item["total_debt_client"]),
                        "summa_total_dollar": self._format_money(item["summa_total_dollar"]),
                        "summa_dollar": self._format_money(item["summa_dollar"]),
                        "summa_naqt": self._format_money(item["summa_naqt"]),
                        "summa_kilik": self._format_money(item["summa_kilik"]),
                        "summa_terminal": self._format_money(item["summa_terminal"]),
                        "summa_transfer": self._format_money(item["summa_transfer"]),
                        "discount_amount": self._format_money(item["discount_amount"]),
                        "zdacha_dollar": self._format_money(item["zdacha_dollar"]),
                    }
                    for item in group["items"]
                ]
            })

        paginator = ResultsSetPagination()
        paginator.set_filter({
            "filial_id": filial_id,
            "client_id": client_id,
            "date_from": request.query_params.get("date_from"),
            "date_to": request.query_params.get("date_to"),
        })

        page = paginator.paginate_queryset(grouped_list, request, view=self)
        serializer = OrdersAndDebtsReportGroupSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)