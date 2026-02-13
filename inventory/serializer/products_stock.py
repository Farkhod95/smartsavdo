from rest_framework import serializers

from accounts.serializers import SkladListSerializer
from inventory.models import ProductStock
from inventory.serializer.product import ProductListSerializer


class ProductStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStock
        fields = ('id', 'product', 'sklad', 'count')
        extra_kwargs = {
            'product': {"required": True},
            'sklad': {"required": True},
            'count': {"required": False, "allow_null": True},
        }


class ProductStockListSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)
    sklad_detail = SkladListSerializer(source='sklad', read_only=True)

    class Meta:
        model = ProductStock
        fields = ('id', 'product', 'product_detail', 'sklad', 'sklad_detail', 'count')
