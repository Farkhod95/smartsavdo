from rest_framework import serializers

from accounts.serializers import FilialListSerializer, RegionListSerializer, \
    DistrictListPublicSerializer
from suppliers.models import Supplier


class SupplierListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    class Meta:
        model = Supplier
        fields = ('id', 'type', 'name', 'filial', 'filial_detail', 'region', 'region_detail', 'district', 'district_detail', 'address', 'inn', 'note', 'is_active', 'is_delete')


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('id', 'type', 'name', 'filial', 'region', 'district', 'address', 'inn', 'note', 'is_active', 'is_delete')