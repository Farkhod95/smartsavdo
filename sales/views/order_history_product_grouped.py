from collections import OrderedDict

from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from sales.models import OrderHistory, OrderHistoryProduct
from sales.serializer.order_history import OrderHistoryListSerializer
from sales.serializer.order_history_product_item import OrderHistoryProductItemSerializer


class OrderHistoryProductByModelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        # 1) OrderHistory
        order_history = get_object_or_404(
            OrderHistory.objects.select_related(
                "order", "client", "employee", "order_filial", "currency", "created_by"
            ),
            pk=pk
            # is_delete=False
        )
        order_history_data = OrderHistoryListSerializer(order_history, context={"request": request}).data

        # 2) Shu history'ga tegishli productlar (tez)
        #    select_related bilan FK larni 1 queryda olib kelamiz
        products_qs = (
            OrderHistoryProduct.objects
            .filter(order_history_id=order_history.pk, is_delete=False)
            .select_related(
                "product",
                "vozvrat_order",
                "sklad",
                "branch",
                "branch_category",
                "model",
                "type",
                "size",
            )
            .order_by("model_id", "id")
        )

        # 3) Serializer (itemlar)
        items = OrderHistoryProductItemSerializer(products_qs, many=True, context={"request": request}).data

        # 4) Python’da model bo‘yicha group qilish (siz xohlagan ko‘rinish)
        grouped = OrderedDict()
        for it in items:
            model_id = it.get("model")
            model_detail = it.get("model_detail") or {}
            model_name = model_detail.get("name") or model_detail.get("name_uz") or model_detail.get("name_ru") or ""

            key = model_id or 0  # model null bo‘lsa 0ga tushiramiz
            if key not in grouped:
                grouped[key] = {
                    "model_id": model_id,
                    "model": model_name if model_id else "Noma’lum model",
                    "product": []
                }
            grouped[key]["product"].append(it)

        return Response({
            "order_history": order_history_data,
            "products": list(grouped.values())
        })
