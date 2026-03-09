from datetime import datetime, time, timedelta

from django.db.models import Count, Sum, Value, DecimalField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from reports.serializers import SoldProductsHistorySerializer
from restapp.pagination import ResultsSetPagination
from sales.models import OrderHistory


class SoldProductsHistoryView(ListAPIView):
    serializer_class = SoldProductsHistorySerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    queryset = OrderHistory.objects.none()

    def _parse_int(self, value, field_name):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError({field_name: f"{field_name} noto‘g‘ri formatda."})

    def _parse_date_value(self, value, field_name):
        """
        Qabul qiladi:
        - 2026-03-08
        - 08.03.2026
        """
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

    def _make_aware_start(self, date_value):
        dt = datetime.combine(date_value, time.min)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def _make_aware_next_day_start(self, date_value):
        dt = datetime.combine(date_value + timedelta(days=1), time.min)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def get_queryset(self):
        user = self.request.user
        filial_id = self.request.query_params.get('filial_id')
        date_from_raw = self.request.query_params.get('date_from')
        date_to_raw = self.request.query_params.get('date_to')

        if not filial_id:
            raise ValidationError({"filial_id": "filial_id yuborilishi shart."})

        filial_id = self._parse_int(filial_id, "filial_id")

        user_filial_ids = set(user.filials.values_list('id', flat=True))
        if filial_id not in user_filial_ids:
            raise ValidationError({"filial_id": "Sizda ushbu filialga dostup yo‘q."})

        date_from = self._parse_date_value(date_from_raw, "date_from")
        date_to = self._parse_date_value(date_to_raw, "date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError({
                "date_to": "date_to date_from dan kichik bo‘lishi mumkin emas."
            })

        decimal_zero = Value(
            0,
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )

        filters = {
            "is_delete": False,
            "is_karzinka": False,
            "order_filial_id": filial_id,
            "created_time__isnull": False,
        }

        queryset = OrderHistory.objects.filter(**filters)

        # created_time bo'yicha filter
        if date_from:
            queryset = queryset.filter(
                created_time__gte=self._make_aware_start(date_from)
            )

        if date_to:
            queryset = queryset.filter(
                created_time__lt=self._make_aware_next_day_start(date_to)
            )

        queryset = (
            queryset
            .annotate(created_date=TruncDate('created_time'))
            .values('created_date')
            .annotate(
                orders_count=Count('id'),
                all_product_summa=Coalesce(
                    Sum('all_product_summa'),
                    decimal_zero,
                    output_field=DecimalField(max_digits=20, decimal_places=2)
                ),
                summa_total_dollar=Coalesce(
                    Sum('summa_total_dollar'),
                    decimal_zero,
                    output_field=DecimalField(max_digits=20, decimal_places=2)
                ),
                all_profit_dollar=Coalesce(
                    Sum('all_profit_dollar'),
                    decimal_zero,
                    output_field=DecimalField(max_digits=20, decimal_places=2)
                ),
            )
            .order_by('-created_date')
        )
        return queryset