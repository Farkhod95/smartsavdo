from rest_framework import serializers

from .models import Region, District, Country, Filial, FilialAccount, Sklad


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


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name', )
        extra_kwargs = {
            'code': {"required": True},
            'name': {"required": True},
        }


class RegionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name', )


class RegionListPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name')


class DistrictListPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'region')


class DistrictListSerializer(serializers.ModelSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)

    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'region', 'region_detail')


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'region')
        extra_kwargs = {
            'code': {"required": True},
            'region': {"required": True},
            'name': {"required": True},
        }


class FilialListSerializer(serializers.ModelSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    class Meta:
        model = Filial
        fields = (
            'id', 'name',
            'region', 'region_detail',
            'district', 'district_detail',
            'address', 'phone_number', 'logo',
            'is_active', 'is_delete'
        )


class FilialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filial
        fields = (
            'id', 'name', 'region', 'district',
            'address', 'phone_number', 'logo',
            'is_active', 'is_delete'
        )


class FilialAccountListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)

    class Meta:
        model = FilialAccount
        fields = ('id', 'filial', 'filial_detail', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class FilialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilialAccount
        fields = ('id', 'filial', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')


class SkladListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    class Meta:
        model = Sklad
        fields = ('id', 'sorting', 'name', 'filial', 'filial_detail', 'region', 'region_detail', 'district', 'district_detail', 'address', 'phone_number', 'is_active', 'is_delete')


class SkladSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sklad
        fields = ('id', 'sorting', 'name', 'filial', 'region', 'district', 'address', 'phone_number', 'is_active', 'is_delete')

    def validate(self, attrs):
        filial = attrs.get("filial") or getattr(self.instance, "filial", None)
        sorting = attrs.get("sorting") if "sorting" in attrs else getattr(self.instance, "sorting", None)

        qs = Sklad.objects.filter(is_delete=False, filial=filial, sorting=sorting)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if filial and sorting is not None and qs.exists():
            raise serializers.ValidationError({
                "sorting": "Bu sorting ushbu filial uchun band. Boshqa raqam tanlang."
            })
        return attrs
