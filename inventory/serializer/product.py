from rest_framework import serializers
from django.conf import settings

from accounts.serializers import FilialListSerializer, FilialSerializer
from inventory.models import ProductImage, Product, ProductTypeSize
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_branch_category import ProductBranchCategorySerializer
from inventory.serializer.product_model import ProductModelListSerializer, ProductModelSerializer
from inventory.serializer.product_type import ProductTypeListSerializer, ProductTypeSerializer
from inventory.serializer.product_type_size import ProductTypeSizeListSerializer, ProductTypeSizeSerializer


class ProductImagePublicSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ('id', 'file')

    def get_file(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request is not None:
                url = request.build_absolute_uri(obj.file.url)
                # HTTP ni HTTPS ga o'zgartirish
                return url.replace('http://', 'https://')
            return obj.file.url
        return None


class ProductListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    images = ProductImagePublicSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'filial_detail', 'branch', 'branch_detail', 'branch_category',
                  'branch_category_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail',
                  'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete', 'images')




class ProductPublicGroupedSerializer(serializers.Serializer):
    filial = serializers.IntegerField(allow_null=True)
    branch = serializers.IntegerField(allow_null=True)
    branch_category = serializers.IntegerField(allow_null=True)
    model = serializers.IntegerField(allow_null=True)
    type = serializers.IntegerField(allow_null=True)

    min_pk = serializers.IntegerField()
    has_image = serializers.BooleanField()

    size_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    filial_detail = serializers.SerializerMethodField()
    branch_detail = serializers.SerializerMethodField()
    branch_category_detail = serializers.SerializerMethodField()
    model_detail = serializers.SerializerMethodField()
    type_detail = serializers.SerializerMethodField()

    node = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()

    # ✅ siz xohlagan field
    images = serializers.SerializerMethodField()

    def _map_get(self, map_name: str, obj_id):
        m = self.context.get(map_name) or {}
        return m.get(obj_id)

    def get_filial_detail(self, obj):
        inst = self._map_get("filial_map", obj.get("filial"))
        return FilialSerializer(inst, context=self.context).data if inst else None

    def get_branch_detail(self, obj):
        inst = self._map_get("branch_map", obj.get("branch"))
        return ProductBranchListSerializer(inst, context=self.context).data if inst else None

    def get_branch_category_detail(self, obj):
        inst = self._map_get("branch_category_map", obj.get("branch_category"))
        return ProductBranchCategorySerializer(inst, context=self.context).data if inst else None

    def get_model_detail(self, obj):
        inst = self._map_get("model_map", obj.get("model"))
        return ProductModelSerializer(inst, context=self.context).data if inst else None

    def get_type_detail(self, obj):
        inst = self._map_get("type_map", obj.get("type"))
        return ProductTypeSerializer(inst, context=self.context).data if inst else None

    def get_sizes(self, obj):
        size_ids = obj.get("size_ids") or []
        size_map = self.context.get("size_map") or {}

        res = []
        for sid in size_ids:
            s = size_map.get(sid)
            if s:
                res.append(ProductTypeSizeSerializer(s, context=self.context).data)
        return res

    def get_node(self, obj):
        size_ids = obj.get("size_ids") or []
        size_map = self.context.get("size_map") or {}

        parts = []
        for sid in size_ids:
            s = size_map.get(sid)
            if not s:
                continue
            unit_name = getattr(s.unit, "name", "") if getattr(s, "unit_id", None) else ""
            parts.append(f"{s.size} {unit_name}".strip())
        return " | ".join(parts) if parts else ""

    def get_images(self, obj):
        # ✅ view payload'dan tayyor url olamiz
        return obj.get("images")


class ProductListOneImageSerializer(serializers.ModelSerializer):
    filial_detail = FilialSerializer(source='filial', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)
    model_detail = ProductModelSerializer(source='model', read_only=True)
    type_detail = ProductTypeSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeSerializer(source='size', read_only=True)

    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'filial_detail', 'branch', 'branch_detail', 'branch_category',
                  'branch_category_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail',
                  'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete', 'images')


    def get_images(self, obj):
        # prefetched bo'lsa bu DB'ga urilmaydi
        first = obj.images.all().order_by('id').first()
        if not first:
            return None
        return ProductImagePublicSerializer(first, context=self.context).data



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete')


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratishdan oldin Product yaratish uchun.
    Client Product'ning barcha kerakli fieldlarini shu yerga yuboradi.
    """
    class Meta:
        model = Product
        fields = (
            'id', 'date', 'reserve_limit', 'filial', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price', 'unit_price',
            'wholesale_price', 'min_price', 'note', 'is_delete',
        )
        read_only_fields = ('id',)