from rest_framework import serializers
from inventory.models import ProductModel
from sales.serializer.order_history_product_item import OrderHistoryProductItemSerializer


class OrderHistoryProductGroupedByModelSerializer(serializers.Serializer):
    model = serializers.CharField(allow_blank=True, allow_null=True)
    model_id = serializers.IntegerField(allow_null=True)
    product = OrderHistoryProductItemSerializer(many=True)
