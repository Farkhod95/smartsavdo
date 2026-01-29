from rest_framework import serializers

from directory.serializers import RegionListPublicSerializer, DistrictListPublicSerializer, CountryListSerializer, \
    ProductCategorySerializer, ModelSerializer, ModelTypeSerializer, ModelSizeSerializer
from .models import FAQ, Product, ProductImage


# Tarjima asosiy serializeri
class LocaleSerializer(serializers.ModelSerializer):
    name_en = serializers.CharField(allow_blank=False)
    name_uz = serializers.CharField(allow_blank=False)
    name_ru = serializers.CharField(allow_blank=False)
    name_lt = serializers.CharField(allow_blank=False)

    title_en = serializers.CharField(allow_blank=False)
    title_uz = serializers.CharField(allow_blank=False)
    title_ru = serializers.CharField(allow_blank=False)
    title_lt = serializers.CharField(allow_blank=False)

    label_en = serializers.CharField(allow_blank=False)
    label_uz = serializers.CharField(allow_blank=False)
    label_ru = serializers.CharField(allow_blank=False)
    label_lt = serializers.CharField(allow_blank=False)

    description_en = serializers.CharField(allow_blank=False)
    description_uz = serializers.CharField(allow_blank=False)
    description_ru = serializers.CharField(allow_blank=False)
    description_lt = serializers.CharField(allow_blank=False)


class BaseLocaleSerializer(serializers.ModelSerializer):
    """
    Dinamik ko‘p tilli serializer:
    Modelda mavjud bo‘lgan *_en/_uz/_ru maydonlar avtomatik qo‘shiladi.
    """
    TRANSLATABLE_BASES = [
        # eng ko‘p uchraydiganlar
        'name', 'title', 'label', 'description',
        'summary', 'caption', 'excerpt', 'body', 'scope',
        'question', 'answer', 'quote', 'author_role', 'company',
    ]
    LANGS = ['en', 'uz', 'ru', 'lt']
    REQUIRED_BASES = {'name', 'title', 'label', 'question', 'answer'}  # muhim maydonlar

    def get_fields(self):
        fields = super().get_fields()
        model = getattr(self.Meta, 'model', None)
        if not model:
            return fields

        # Modeldagi real maydonlar to‘plami
        model_field_names = {f.name for f in model._meta.get_fields()}

        for base in self.TRANSLATABLE_BASES:
            for lang in self.LANGS:
                f_name = f"{base}_{lang}"
                if f_name in model_field_names:
                    fields[f_name] = serializers.CharField(
                        allow_blank=False,
                        required=(base in self.REQUIRED_BASES)
                    )
        return fields


class ProductImagePublicSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'file')


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'category', 'model', 'model_type', 'model_size', 'size', 'type', 'count', 'real_price', 'price',
                  'sorting', 'is_delete', 'discription')


class ProductListSerializer(serializers.ModelSerializer):
    category_detail = ProductCategorySerializer(source='category', read_only=True)
    model_detail = ModelSerializer(source='model', read_only=True)
    model_type_detail = ModelTypeSerializer(source='model_type', read_only=True)
    model_size_detail = ModelSizeSerializer(source='model_size', read_only=True)

    attachments = ProductImagePublicSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'category', 'category_detail', 'model', 'model_detail', 'model_type', 'model_type_detail',
                  'model_size', 'model_size_detail', 'size', 'type', 'count', 'real_price', 'price',
                  'sorting', 'is_delete', 'discription', 'attachments', )


class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'file')


class ProductImageListSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)


    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'product_detail', 'file')


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
        read_only_fields = ('id', 'created_time', 'updated_time', 'created_by', 'updated_by')
