from rest_framework import serializers
from django.db import transaction
from inventory.models import ProductType, ProductTypeSize
from inventory.serializer.product_model import ProductModelListSerializer
from inventory.serializer.unit import UnitListSerializer


class ProductTypeListSerializer(serializers.ModelSerializer):
    madel_detail = ProductModelListSerializer(source='madel', read_only=True)

    # ✅ BranchCategory (id + name)
    # branch_category = serializers.IntegerField(source='madel.branch_category_id', read_only=True)
    branch_category_name = serializers.CharField(source='madel.branch_category.name', read_only=True)

    # ✅ ProductBranch (id + name)
    # product_branch = serializers.IntegerField(source='madel.branch_category.product_branch_id', read_only=True)
    branch_name = serializers.CharField(source='madel.branch_category.product_branch.name', read_only=True)

    class Meta:
        model = ProductType
        fields = ('id', 'name', 'branch_name', 'branch_category_name', 'madel', 'madel_detail', 'sorting', 'is_delete')


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ('id', 'name', 'madel', 'sorting', 'is_delete')

    def _suggest_sorting_first_free(self, madel_id: int) -> int:
        used = (
            ProductType.objects
            .filter(is_delete=False, madel_id=madel_id, sorting__isnull=False)
            .order_by('sorting')
            .values_list('sorting', flat=True)
        )

        suggested = 1
        for s in used:
            try:
                s_int = int(s)
            except (TypeError, ValueError):
                continue

            if s_int < suggested:
                continue
            if s_int == suggested:
                suggested += 1
            else:
                break

        return suggested

    def validate(self, attrs):
        madel = attrs.get('madel', getattr(self.instance, 'madel', None))
        sorting = attrs.get('sorting', getattr(self.instance, 'sorting', None))
        is_delete = attrs.get('is_delete', getattr(self.instance, 'is_delete', False))

        # sorting null bo'lsa unique tekshiruv yo'q
        if madel is None or sorting is None:
            return attrs

        # o'chirilayotgan bo'lsa tekshirmaymiz
        if is_delete is True:
            return attrs

        qs = ProductType.objects.filter(
            madel=madel,
            sorting=sorting,
            is_delete=False
        )

        # PUT/UPDATE paytida o'zini exclude
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            suggestion = self._suggest_sorting_first_free(madel_id=madel.id)
            raise serializers.ValidationError({
                "sorting": f"Bu tartib raqam band. Bo‘sh tartib raqam: {suggestion}"
            })

        return attrs




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