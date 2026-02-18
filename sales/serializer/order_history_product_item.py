from rest_framework import serializers
from sales.models import OrderHistoryProduct

from inventory.serializer.product import ProductSerializer
from inventory.serializer.product_model import ProductModelListSerializer
from inventory.serializer.product_type import ProductTypeListSerializer
from inventory.serializer.product_type_size import ProductTypeSizeListSerializer
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_branch_category import ProductBranchCategoryForSerializer
from sales.serializer.vozvrat_order import VozvratOrderSerializer


class OrderHistoryProductItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)
    vozvrat_order_detail = VozvratOrderSerializer(source="vozvrat_order", read_only=True)

    branch_detail = ProductBranchListSerializer(source="branch", read_only=True)
    branch_category_detail = ProductBranchCategoryForSerializer(source="branch_category", read_only=True)

    model_detail = ProductModelListSerializer(source="model", read_only=True)
    type_detail = ProductTypeListSerializer(source="type", read_only=True)
    size_detail = ProductTypeSizeListSerializer(source="size", read_only=True)

    class Meta:
        model = OrderHistoryProduct
        fields = (
            "id", "date",
            "order_history",
            "product", "product_detail",
            "vozvrat_order", "vozvrat_order_detail",
            "sklad",
            "branch", "branch_detail",
            "branch_category", "branch_category_detail",
            "model", "model_detail",
            "type", "type_detail",
            "size", "size_detail",
            "count", "given_count",
            "price_dollar", "price_sum",
            "real_price", "unit_price", "wholesale_price",
            "is_delete", "cargo_terminal",
            "price_difference", "status_order", "is_karzinka",
        )
