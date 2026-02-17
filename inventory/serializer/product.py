from rest_framework import serializers

from accounts.serializers import FilialListSerializer, FilialSerializer
from inventory.models import ProductImage, Product
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
                  'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete', 'images',
                  'is_active')


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
                  'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete', 'images',
                  'is_active')


    def get_images(self, obj):
        # prefetched bo'lsa bu DB'ga urilmaydi
        first = obj.images.all().order_by('id').first()
        if not first:
            return None
        return ProductImagePublicSerializer(first, context=self.context).data



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'branch', 'branch_category', 'model', 'type', 'size', 'count',
                  'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete', 'is_active')


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratishdan oldin Product yaratish uchun.
    Client Product'ning barcha kerakli fieldlarini shu yerga yuboradi.
    """
    class Meta:
        model = Product
        fields = (
            'id', 'date', 'reserve_limit', 'filial', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price', 'unit_price',
            'wholesale_price', 'min_price', 'note', 'is_delete', 'is_active'
        )
        read_only_fields = ('id',)