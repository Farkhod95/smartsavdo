from rest_framework import serializers

from inventory.models import ProductImage
from inventory.serializer.product import ProductListSerializer


class ProductImageListSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'product_detail', 'file')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'file')