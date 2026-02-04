from rest_framework import serializers
from django.db import transaction

from accounts.serializers import FilialListSerializer
from inventory.models import Unit, ProductBranch, ProductModel, ProductType, ProductTypeSize, Product, ProductHistory, \
    ProductImage
from suppliers.serializers import PurchaseInvoiceSerializer


class UnitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ('id', 'code', 'name', 'is_active')


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ('id', 'code', 'name', 'is_active')


class ProductBranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranch
        fields = ('id', 'name', 'sorting', 'is_delete')


class ProductBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranch
        fields = ('id', 'name', 'sorting', 'is_delete')


class ProductModelListSerializer(serializers.ModelSerializer):
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)

    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch', 'branch_detail', 'sorting', 'is_delete')


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch', 'sorting', 'is_delete')


class ProductTypeListSerializer(serializers.ModelSerializer):
    madel_detail = ProductModelListSerializer(source='madel', read_only=True)

    class Meta:
        model = ProductType
        fields = ('id', 'name', 'madel', 'madel_detail', 'sorting', 'is_delete')


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ('id', 'name', 'madel', 'sorting', 'is_delete')


class ProductTypeSizeListSerializer(serializers.ModelSerializer):
    product_type_detail = ProductTypeListSerializer(source='product_type', read_only=True)
    type_detail = UnitListSerializer(source='type', read_only=True)

    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'product_type_detail', 'size', 'type', 'type_detail', 'sorting', 'is_delete')


class ProductTypeSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'size', 'type', 'sorting', 'is_delete')


class ProductImagePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'file')


class ProductListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'filial_detail', 'branch', 'branch_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete')


class ProductListPublicSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    images = ProductImagePublicSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'filial_detail', 'branch', 'branch_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete', 'images')



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'date', 'reserve_limit', 'filial', 'branch', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete')


class ProductHistoryListSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)
    purchase_invoice_detail = PurchaseInvoiceSerializer(source='purchase_invoice', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'product_detail', 'purchase_invoice', 'purchase_invoice_detail', 'branch', 'branch_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')


class ProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'purchase_invoice', 'branch', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')

class ProductCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratishdan oldin Product yaratish uchun.
    Client Product'ning barcha kerakli fieldlarini shu yerga yuboradi.
    """
    class Meta:
        model = Product
        fields = (
            'id', 'date', 'reserve_limit', 'filial', 'branch', 'model', 'type', 'size', 'count', 'real_price', 'unit_price',
            'wholesale_price', 'min_price', 'note', 'is_delete',
        )
        read_only_fields = ('id',)


class ProductHistoryCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratadi, lekin product maydoni o‘rniga product_data qabul qiladi.
    """
    # product_data = ProductCreateSerializer(write_only=True)

    class Meta:
        model = ProductHistory
        fields = (
            'id', 'date', 'reserve_limit', 'purchase_invoice', 'branch', 'model', 'type', 'size', 'count', 'real_price',
            'unit_price', 'wholesale_price', 'min_price', 'note',
            'product',       # response’da ko‘rinsin
            # 'product_data',  # request’da keladi
        )
        read_only_fields = ('id', 'product')

    def validate(self, attrs):
        """
        Ixtiyoriy: product_data ichidagi branch/model/type/size
        history dagi branch/model/type/size bilan mosligini tekshirsa ham bo‘ladi.
        (Ko‘p loyihalarda shu muhim.)
        """
        product_data = attrs.get('product_data') or {}
        for f in ('branch', 'model', 'type', 'size'):
            v_hist = attrs.get(f)
            v_prod = product_data.get(f)
            if v_hist and v_prod and v_hist != v_prod:
                raise serializers.ValidationError({
                    f: f"History dagi {f} Product dagi {f} bilan mos emas."
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        product_data = validated_data.pop('product_data')

        # 1) Product yaratamiz
        product = Product.objects.create(**product_data)

        # 2) ProductHistory yaratamiz
        history = ProductHistory.objects.create(
            product=product,
            **validated_data
        )
        return history


class ProductImageListSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'product_detail', 'file')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'file')