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
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)

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
    unit_code = serializers.SerializerMethodField()

    class Meta:
        model = ProductTypeSize
        fields = ('id', 'product_type', 'size', 'unit', 'unit_code', 'sorting', 'is_delete')

    def get_unit_code(self, obj):
        # Unit.name ni qaytaradi (Unit yo'q bo'lsa None)
        return obj.unit.code if obj.unit else None


# ============================== ProductType Create Start===================================================
class ProductTypeSizeCreateSerializer(serializers.Serializer):
    size = serializers.FloatField(required=False, allow_null=True)
    unit = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        # size yoki unit yo‘q bo‘lsa, buni "bo‘sh item" deb hisoblaymiz
        # view/parent serializerda bunday itemlarni skip qilamiz
        return attrs


class ProductTypeCreateItemSerializer(serializers.Serializer):
    madel = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sorting = serializers.IntegerField(required=False, allow_null=True, default=0)
    product_type_size = ProductTypeSizeCreateSerializer(many=True, required=False)

    def validate_name(self, value):
        if value is None:
            return value
        value = value.strip()
        return value

    @transaction.atomic
    def create(self, validated_data):
        sizes_data = validated_data.pop('product_type_size', []) or []

        # ProductType yaratamiz
        product_type = ProductType.objects.create(
            madel_id=validated_data.get('madel'),
            name=validated_data.get('name'),
            sorting=validated_data.get('sorting') if validated_data.get('sorting') is not None else 0,
            is_delete=False,
        )

        # ProductTypeSize larni tayyorlaymiz (bo‘shlarini tashlab ketamiz)
        size_objects = []
        for s in sizes_data:
            size_val = s.get('size', None)
            unit_val = s.get('unit', None)

            # ikkalasi ham bo‘sh bo‘lsa skip
            if size_val in (None, "") and unit_val in (None, ""):
                continue

            # unit bo‘sh bo‘lsa ham saqlash kerak bo‘lsa, allow_null=True bo‘lgani uchun o‘tadi
            # xohlasangiz unit majburiy qiling (unit=None bo‘lsa error)
            size_objects.append(
                ProductTypeSize(
                    product_type=product_type,
                    size=size_val if size_val != "" else None,
                    unit_id=unit_val if unit_val != "" else None,
                    sorting=0,
                    is_delete=False,
                )
            )

        if size_objects:
            ProductTypeSize.objects.bulk_create(size_objects)

        return product_type


class ProductTypeBulkCreateSerializer(serializers.ListSerializer):
    """
    Request: [ {...}, {...} ]
    Shu ListSerializer listni qabul qiladi.
    """
    child = ProductTypeCreateItemSerializer()

    @transaction.atomic
    def create(self, validated_data):
        created = []
        for item in validated_data:
            created.append(self.child.create(item))
        return created


class ProductTypeBulkCreateResponseSerializer(serializers.ModelSerializer):
    """
    Javob qaytarishda qulay bo‘lishi uchun:
    - ProductType
    - unga bog‘langan size lar
    """
    product_type_sizes = serializers.SerializerMethodField()

    class Meta:
        model = ProductType
        fields = ("id", "name", "madel", "sorting", "is_delete", "product_type_sizes")

    def get_product_type_sizes(self, obj):
        qs = obj.product_type_sizes.all().order_by("id")
        return [
            {
                "id": x.id,
                "size": x.size,
                "unit": x.unit_id,
                "sorting": x.sorting,
                "is_delete": x.is_delete,
            }
            for x in qs
        ]



# ============================== ProductType Create End===================================================



# =================== GET uchun (front format) ===================

class ProductTypeSizeOutSerializer(serializers.ModelSerializer):
    # front siz xohlagan: size, unit
    # xohlasangiz unit_detail ham qo‘shib beramiz
    unit_detail = UnitListSerializer(source='unit', read_only=True)

    class Meta:
        model = ProductTypeSize
        fields = ("id", "size", "unit", "unit_detail", "sorting", "is_delete")


class ProductTypeOutSerializer(serializers.ModelSerializer):
    madel_detail = ProductModelListSerializer(source='madel', read_only=True)
    product_type_size = serializers.SerializerMethodField()

    class Meta:
        model = ProductType
        fields = ("id", "madel", "madel_detail", "name", "sorting", "is_delete", "product_type_size")

    def get_product_type_size(self, obj):
        qs = obj.product_type_sizes.all().order_by("sorting", "id")
        return ProductTypeSizeOutSerializer(qs, many=True, context=self.context).data


# =================== PUT uchun (update payload) ===================

class ProductTypeSizeUpsertSerializer(serializers.Serializer):
    """
    PUT payload ichida:
    - mavjudni update qilish uchun: {"id": 5, "size": 12, "unit": 1}
    - yangi qo‘shish uchun: {"size": 64, "unit": 1}
    """
    id = serializers.IntegerField(required=False)
    size = serializers.FloatField(required=False, allow_null=True)
    unit = serializers.IntegerField(required=False, allow_null=True)
    sorting = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        return attrs


class ProductTypeUpdateSerializer(serializers.ModelSerializer):
    product_type_size = ProductTypeSizeUpsertSerializer(many=True, required=False)

    class Meta:
        model = ProductType
        fields = ("madel", "name", "sorting", "is_delete", "product_type_size")

    @transaction.atomic
    def update(self, instance, validated_data):
        sizes_data = validated_data.pop("product_type_size", None)

        # 1) ProductType update
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        # 2) ProductTypeSize update/create/delete
        if sizes_data is not None:
            existing_qs = ProductTypeSize.objects.filter(product_type=instance)
            existing_map = {x.id: x for x in existing_qs}

            keep_ids = set()
            create_objs = []

            for item in sizes_data:
                size_id = item.get("id")

                # bo‘sh itemlarni skip
                size_val = item.get("size", None)
                unit_val = item.get("unit", None)

                if (size_id is None) and (size_val in (None, "") and unit_val in (None, "")):
                    continue

                if size_id and size_id in existing_map:
                    obj = existing_map[size_id]
                    # update
                    if "size" in item:
                        obj.size = size_val if size_val != "" else None
                    if "unit" in item:
                        obj.unit_id = unit_val if unit_val != "" else None
                    if "sorting" in item:
                        obj.sorting = item.get("sorting") if item.get("sorting") is not None else obj.sorting
                    obj.save()
                    keep_ids.add(obj.id)
                else:
                    # create new
                    create_objs.append(
                        ProductTypeSize(
                            product_type=instance,
                            size=size_val if size_val != "" else None,
                            unit_id=unit_val if unit_val != "" else None,
                            sorting=item.get("sorting") if item.get("sorting") is not None else 0,
                            is_delete=False,
                        )
                    )

            if create_objs:
                ProductTypeSize.objects.bulk_create(create_objs)
                # bulk_create dan keyin keep_ids ga qo‘shish shart emas,
                # chunki pastdagi delete faqat oldingi existing_qs ichida ishlaydi.

            # 3) payload'da kelmagan eski sizelarni delete qilish
            # faqat oldingi mavjudlardan kelmaganlarini o‘chiramiz
            to_delete_ids = [obj_id for obj_id in existing_map.keys() if obj_id not in keep_ids]
            if to_delete_ids:
                ProductTypeSize.objects.filter(id__in=to_delete_ids).delete()

        return instance


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