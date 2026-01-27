from rest_framework import serializers

from .models import Region, District, Country, ProductCategory, Model, ModelType, ModelSize


# Tarjima asosiy serializeri
class LocaleSerializer(serializers.ModelSerializer):
    name_en = serializers.CharField(allow_blank=False)
    name_uz = serializers.CharField(allow_blank=False)
    name_ru = serializers.CharField(allow_blank=False)
    name_lt = serializers.CharField(allow_blank=False)


class CountrySerializer(LocaleSerializer):
    class Meta:
        model = Country
        fields = ('id', 'code', 'name', )
        extra_kwargs = {
            'code': {"required": True},
            'name': {"required": True},
        }


class CountryListSerializer(LocaleSerializer):
    class Meta:
        model = Country
        fields = ('id', 'code', 'name')


class RelatedRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'name')


class RelatedDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'name')


class RelatedPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'name')


class RegionSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name', )
        extra_kwargs = {
            'code': {"required": True},
            'name': {"required": True},
        }


class RegionListSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name', )


class RegionListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name')


class DistrictListPublicSerializer(LocaleSerializer):
    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'region')


class DistrictListSerializer(LocaleSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)

    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'region', 'region_detail')


class DistrictSerializer(LocaleSerializer):
    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'region')
        extra_kwargs = {
            'code': {"required": True},
            'region': {"required": True},
            'name': {"required": True},
        }


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'sorting', 'is_delete')


class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = ('id', 'name', 'category', 'sorting', 'is_delete')


class ModelListSerializer(serializers.ModelSerializer):
    category_detail = ProductCategorySerializer(source='category', read_only=True)

    class Meta:
        model = Model
        fields = ('id', 'name', 'category', 'category_detail', 'sorting', 'is_delete')


class ModelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelType
        fields = ('id', 'name', 'model', 'sorting', 'is_delete')


class ModelTypeListSerializer(serializers.ModelSerializer):
    model_detail = ModelSerializer(source='model', read_only=True)

    class Meta:
        model = ModelType
        fields = ('id', 'name', 'model', 'model_detail', 'sorting', 'is_delete')


class ModelSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelSize
        fields = ('id', 'model_type', 'size', 'type', 'sorting', 'is_delete')


class ModelSizeListSerializer(serializers.ModelSerializer):
    model_type_detail = ModelTypeSerializer(source='model_type', read_only=True)


    class Meta:
        model = ModelSize
        fields = ('id', 'model_type', 'model_type_detail', 'size', 'type', 'sorting', 'is_delete')