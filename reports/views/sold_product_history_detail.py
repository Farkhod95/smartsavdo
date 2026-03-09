from datetime import datetime, time, timedelta

from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from reports.serializers import SoldOrderItemSerializer, DebtRepaymentItemSerializer
from sales.models import OrderHistory
from finance.models import DebtRepayment



class SoldProductsHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def _parse_int(self, value, field_name):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError({field_name: f"{field_name} noto‘g‘ri formatda."})

    def _parse_date_value(self, value):
        """
        Qabul qiladi:
        - 2026-03-08
        - 08.03.2026
        """
        if not value:
            raise ValidationError({"date": "date yuborilishi shart."})

        parsed = parse_date(value)
        if parsed:
            return parsed

        try:
            return datetime.strptime(value, "%d.%m.%Y").date()
        except Exception:
            raise ValidationError({
                "date": "date formati noto‘g‘ri. Masalan: 2026-03-08 yoki 08.03.2026"
            })

    def _get_day_range(self, date_value):
        """
        created_time bo'yicha kun oralig'i:
        [kun boshi, keyingi kun boshi)
        """
        start_dt = datetime.combine(date_value, time.min)
        end_dt = start_dt + timedelta(days=1)

        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())

        return start_dt, end_dt

    def _money_zero(self):
        return Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))

    def _get_user_filial_ids(self, user):
        return set(user.filials.values_list("id", flat=True))

    def _build_totals(self, queryset):
        zero = self._money_zero()
        return queryset.aggregate(
            summa_total_dollar=Coalesce(
                Sum("summa_total_dollar"),
                zero,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            summa_dollar=Coalesce(
                Sum("summa_dollar"),
                zero,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            summa_naqt=Coalesce(
                Sum("summa_naqt"),
                zero,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            summa_kilik=Coalesce(
                Sum("summa_kilik"),
                zero,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            summa_terminal=Coalesce(
                Sum("summa_terminal"),
                zero,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            summa_transfer=Coalesce(
                Sum("summa_transfer"),
                zero,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
        )

    def get(self, request, *args, **kwargs):
        user = request.user

        filial_id = self._parse_int(request.query_params.get("filial_id"), "filial_id")
        date_value = self._parse_date_value(request.query_params.get("date"))

        client_id_raw = request.query_params.get("client_id")
        client_id = None
        if client_id_raw not in [None, ""]:
            client_id = self._parse_int(client_id_raw, "client_id")

        user_filial_ids = self._get_user_filial_ids(user)
        if filial_id not in user_filial_ids:
            raise ValidationError({"filial_id": "Sizda ushbu filialga dostup yo‘q."})

        day_start, day_end = self._get_day_range(date_value)

        order_qs = (
            OrderHistory.objects
            .filter(
                is_delete=False,
                is_karzinka=False,
                order_filial_id=filial_id,
                created_time__gte=day_start,
                created_time__lt=day_end,
            )
            .select_related("client", "employee")
            .order_by("created_time", "id")
        )

        debt_qs = (
            DebtRepayment.objects
            .filter(
                is_delete=False,
                # debt_status=True,
                filial_id=filial_id,
                created_time__gte=day_start,
                created_time__lt=day_end,
            )
            .select_related("client", "employee")
            .order_by("created_time", "id")
        )

        if client_id is not None:
            order_qs = order_qs.filter(client_id=client_id)
            debt_qs = debt_qs.filter(client_id=client_id)

        order_items = []
        for obj in order_qs:
            order_items.append({
                "id": obj.id,
                "client_id": obj.client_id,
                "client_name": getattr(obj.client, "full_name", None),
                "employee_id": obj.employee_id,
                "employee_name": getattr(obj.employee, "username", None),
                "time": obj.created_time.strftime("%H:%M") if obj.created_time else None,
                "datetime": obj.created_time,
                "note": obj.note,
                "driver_info": obj.driver_info,
                "all_product_summa": obj.all_product_summa,
                "summa_total_dollar": obj.summa_total_dollar,
                "summa_dollar": obj.summa_dollar,
                "summa_naqt": obj.summa_naqt,
                "summa_kilik": obj.summa_kilik,
                "summa_terminal": obj.summa_terminal,
                "summa_transfer": obj.summa_transfer,
                "all_profit_dollar": obj.all_profit_dollar,
            })

        debt_items = []
        for obj in debt_qs:
            debt_items.append({
                "id": obj.id,
                "client_id": obj.client_id,
                "client_name": getattr(obj.client, "full_name", None),
                "employee_id": obj.employee_id,
                "employee_name": getattr(obj.employee, "username", None),
                "time": obj.created_time.strftime("%H:%M") if obj.created_time else None,
                "datetime": obj.created_time,
                "note": obj.note,
                "old_total_debt_client": obj.old_total_debt_client,
                "total_debt_client": obj.total_debt_client,
                "summa_total_dollar": obj.summa_total_dollar,
                "summa_dollar": obj.summa_dollar,
                "summa_naqt": obj.summa_naqt,
                "summa_kilik": obj.summa_kilik,
                "summa_terminal": obj.summa_terminal,
                "summa_transfer": obj.summa_transfer,
            })

        response_data = {
            "date": date_value,
            "date_label": date_value.strftime("%d.%m.%Y"),
            "filial_id": filial_id,
            "client_id": client_id,
            "orders": {
                "count": len(order_items),
                "results": SoldOrderItemSerializer(order_items, many=True).data,
                "totals": self._build_totals(order_qs),
            },
            "debt_repayments": {
                "count": len(debt_items),
                "results": DebtRepaymentItemSerializer(debt_items, many=True).data,
                "totals": self._build_totals(debt_qs),
            },
        }

        return Response(response_data)