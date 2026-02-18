from rest_framework import serializers
from sales.models import OrderHistoryProduct

from inventory.serializer.product import ProductSerializer
from inventory.serializer.product_model import ProductModelForSerializer
from inventory.serializer.product_type import ProductTypeForSerializer
from inventory.serializer.product_type_size import ProductTypeSizeForSerializer
from inventory.serializer.product_branch import ProductBranchForSerializer
from inventory.serializer.product_branch_category import ProductBranchCategoryForSerializer
from sales.serializer.vozvrat_order import VozvratOrderSerializer


class OrderHistoryProductItemSerializer(serializers.ModelSerializer):
    # product_detail = ProductSerializer(source="product", read_only=True)
    vozvrat_order_detail = VozvratOrderSerializer(source="vozvrat_order", read_only=True)

    branch_detail = ProductBranchForSerializer(source="branch", read_only=True)
    branch_category_detail = ProductBranchCategoryForSerializer(source="branch_category", read_only=True)

    model_detail = ProductModelForSerializer(source="model", read_only=True)
    type_detail = ProductTypeForSerializer(source="type", read_only=True)
    size_detail = ProductTypeSizeForSerializer(source="size", read_only=True)

    class Meta:
        model = OrderHistoryProduct
        fields = (
            "id", "date",
            "order_history",
            "product",
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
