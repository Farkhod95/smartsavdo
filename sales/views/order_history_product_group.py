from decimal import Decimal

from django.db.models import Sum, Value, IntegerField, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from sales.models import OrderHistory, OrderHistoryProduct
from sales.serializer.order_history import OrderHistoryListSerializer

from inventory.models import ProductModel, ProductBranch, ProductBranchCategory
from sales.serializer.order_history_product_group import OrderHistoryProductByModelGroupSerializer


class OrderHistoryProductByModelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        order_history = get_object_or_404(
            OrderHistory.objects.select_related(
                "order", "client", "employee", "order_filial", "currency", "created_by"
            ),
            pk=pk,
            is_delete=False
        )

        order_history_data = OrderHistoryListSerializer(order_history, context={"request": request}).data

        # DecimalField lar uchun 0 ni Decimal qilib, output_field ni aniq beramiz
        money_field = DecimalField(max_digits=20, decimal_places=2)

        qs = (
            OrderHistoryProduct.objects
            .filter(order_history_id=order_history.pk, is_delete=False)
            .values("model_id", "branch_id", "branch_category_id")
            .annotate(
                total_count=Coalesce(Sum("count"), Value(0), output_field=IntegerField()),
                total_given_count=Coalesce(Sum("given_count"), Value(0), output_field=IntegerField()),

                total_price_sum=Coalesce(
                    Sum("price_sum", output_field=money_field),
                    Value(Decimal("0.00")),
                    output_field=money_field
                ),
                total_price_dollar=Coalesce(
                    Sum("price_dollar", output_field=money_field),
                    Value(Decimal("0.00")),
                    output_field=money_field
                ),

                type_ids=ArrayAgg("type_id", distinct=True),
                size_ids=ArrayAgg("size_id", distinct=True),
                product_ids=ArrayAgg("id", distinct=True),
            )
            .order_by("model_id")
        )

        group_rows = list(qs)

        model_ids = [r["model_id"] for r in group_rows if r["model_id"]]
        branch_ids = [r["branch_id"] for r in group_rows if r["branch_id"]]
        bc_ids = [r["branch_category_id"] for r in group_rows if r["branch_category_id"]]

        models_map = ProductModel.objects.in_bulk(model_ids) if model_ids else {}
        branch_map = ProductBranch.objects.in_bulk(branch_ids) if branch_ids else {}
        branch_category_map = ProductBranchCategory.objects.in_bulk(bc_ids) if bc_ids else {}

        products_grouped = OrderHistoryProductByModelGroupSerializer(
            group_rows,
            many=True,
            context={
                "request": request,
                "models_map": models_map,
                "branch_map": branch_map,
                "branch_category_map": branch_category_map,
            }
        ).data

        return Response({
            "order_history": order_history_data,
            "products": products_grouped
        })
