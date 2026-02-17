from rest_framework import serializers
from accounts.serializers import RegionListSerializer, DistrictListPublicSerializer, FilialListSerializer
from sales.models import Client


class ClientListSerializer(serializers.ModelSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)
    filial_detail = FilialListSerializer(source='filial', read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'telegram_id', 'full_name', 'is_active', 'date_of_birthday', 'gender', 'phone_number', 'region',
                  'region_detail', 'district', 'district_detail', 'filial', 'filial_detail', 'total_debt', 'keshbek',
                  'is_profit_loss', 'type', 'is_delete')


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'telegram_id', 'full_name', 'is_active', 'date_of_birthday', 'gender', 'phone_number', 'region',
                  'district', 'filial', 'total_debt', 'keshbek', 'is_profit_loss', 'type', 'is_delete')
