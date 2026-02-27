from rest_framework import serializers
from accounts.serializers import FilialListSerializer, RegionListSerializer, \
    DistrictListPublicSerializer
from suppliers.models import Supplier, SupplierAccount


class SupplierSerializer(serializers.ModelSerializer):
    # ✅ annotate qilingan filial_debt_db ni chiqaramiz
    filial_debt = serializers.DecimalField(
        source='filial_debt_db',
        max_digits=20,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Supplier
        fields = (
            'id', 'type', 'name', 'filial', 'region', 'district',
            'address', 'inn', 'note', 'is_active', 'is_delete',
            'filial_debt',
        )


class SupplierListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    # ✅ annotate qilingan filial_debt_db ni chiqaramiz
    filial_debt = serializers.DecimalField(
        source='filial_debt_db',
        max_digits=20,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Supplier
        fields = (
            'id', 'type', 'name',
            'filial', 'filial_detail',
            'region', 'region_detail',
            'district', 'district_detail',
            'address', 'inn', 'note',
            'is_active', 'is_delete',
            'filial_debt',
        )