from django.db.models import Count, Sum, Value, DecimalField
from django.db.models.functions import Coalesce, TruncDate
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

    def get_queryset(self):
        user = self.request.user
        filial_id = self.request.query_params.get('filial_id')

        if not filial_id:
            raise ValidationError({"filial_id": "filial_id yuborilishi shart."})

        try:
            filial_id = int(filial_id)
        except (TypeError, ValueError):
            raise ValidationError({"filial_id": "filial_id noto‘g‘ri formatda."})

        user_filial_ids = set(user.filials.values_list('id', flat=True))
        if filial_id not in user_filial_ids:
            raise ValidationError({"filial_id": "Sizda ushbu filialga dostup yo‘q."})

        decimal_zero = Value(
            0,
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )

        queryset = (
            OrderHistory.objects
            .filter(
                is_delete=False,
                is_karzinka=False,
                order_filial_id=filial_id,
                created_time__isnull=False,
            )
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