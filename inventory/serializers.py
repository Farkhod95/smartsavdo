from rest_framework import serializers
from django.db import transaction

from accounts.serializers import FilialListSerializer, FilialSerializer
from inventory.models import Unit, ProductBranch, ProductModel, ProductType, ProductTypeSize, Product, ProductHistory, \
    ProductImage, ProductBranchCategory
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


class ProductBranchCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranchCategory
        fields = ('id', 'product_branch', 'name', 'sorting', 'is_delete')
        extra_kwargs = {
            'name': {"required": False, "allow_blank": True, "allow_null": True},
            'sorting': {"required": False, "allow_null": True},
            'is_delete': {"required": False},
        }


class ProductBranchCategoryListSerializer(serializers.ModelSerializer):
    product_branch_detail = ProductBranchListSerializer(source='product_branch', read_only=True)

    class Meta:
        model = ProductBranchCategory
        fields = ('id', 'product_branch', 'product_branch_detail', 'name', 'sorting', 'is_delete')


class ProductModelListSerializer(serializers.ModelSerializer):
    branch_category_detail = ProductBranchCategorySerializer(source='branch', read_only=True)

    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch_category', 'branch_category_detail', 'sorting', 'is_delete')


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch_category', 'sorting', 'is_delete')


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
    unit_detail = UnitListSerializer(source='unit', read_only=True)


    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'product_type_detail', 'size', 'unit', 'unit_detail', 'sorting', 'is_delete')


class ProductTypeSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'size', 'unit', 'sorting', 'is_delete')


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


class ProductHistoryListSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)
    purchase_invoice_detail = PurchaseInvoiceSerializer(source='purchase_invoice', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'filial', 'product_detail', 'purchase_invoice', 'purchase_invoice_detail', 'branch', 'branch_detail', 'branch_category', 'branch_category_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')


class ProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'filial', 'purchase_invoice', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')

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


class ProductHistoryCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratadi, lekin product maydoni o‘rniga product_data qabul qiladi.
    """
    # product_data = ProductCreateSerializer(write_only=True)

    class Meta:
        model = ProductHistory
        fields = (
            'id', 'date', 'filial', 'reserve_limit', 'purchase_invoice', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price',
            'unit_price', 'wholesale_price', 'min_price', 'note',
            'product',       # response’da ko‘rinsin
            # 'product_data',  # request’da keladi
        )
        read_only_fields = ('id', 'product')

    def validate(self, attrs):
        """
        filial payload’da kelmasa, purchase_invoice.filial dan olib qo'yamiz.
        Ikkalasi ham bo'lmasa xato.
        """
        filial = attrs.get('filial')
        invoice = attrs.get('purchase_invoice')

        if not filial:
            if invoice and getattr(invoice, 'filial_id', None):
                attrs['filial'] = invoice.filial
            else:
                raise serializers.ValidationError({
                    'filial': "Filial yuborilishi kerak yoki purchase_invoice ichida filial bo‘lishi shart."
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # filial endi aniq bor (validate ichida qo‘yilgan bo‘ladi)
        filial = validated_data['filial']

        # 1) Product yaratamiz (payload fieldlari asosida)
        product = Product.objects.create(
            date=validated_data.get('date'),
            reserve_limit=validated_data.get('reserve_limit'),
            filial=filial,
            branch=validated_data.get('branch'),
            branch_category=validated_data.get('branch_category'),
            model=validated_data.get('model'),
            type=validated_data.get('type'),
            size=validated_data.get('size'),
            count=validated_data.get('count'),
            real_price=validated_data.get('real_price', 0),
            unit_price=validated_data.get('unit_price', 0),
            wholesale_price=validated_data.get('wholesale_price', 0),
            min_price=validated_data.get('min_price', 0),
            note=validated_data.get('note'),
            is_delete=False,
        )

        # 2) ProductHistory yaratamiz va product ni bog'laymiz
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