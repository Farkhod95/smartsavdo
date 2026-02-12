from rest_framework import serializers

from inventory.models import ProductTypeSize
from inventory.serializer.product_type import ProductTypeListSerializer
from inventory.serializer.unit import UnitListSerializer


class ProductTypeSizeListSerializer(serializers.ModelSerializer):
    product_type_detail = ProductTypeListSerializer(source='product_type', read_only=True)
    unit_detail = UnitListSerializer(source='unit', read_only=True)


    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'product_type_detail', 'size', 'unit', 'unit_detail', 'sorting', 'is_delete')


class ProductTypeSizeSerializer(serializers.ModelSerializer):
    unit_code = serializers.SerializerMethodField()

    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'size', 'unit', 'unit_code', 'sorting', 'is_delete')

    def get_unit_code(self, obj):
        # Unit.name ni qaytaradi (Unit yo'q bo'lsa None)
        return obj.unit.code if obj.unit else None