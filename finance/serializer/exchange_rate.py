from rest_framework import serializers

from accounts.serializers import FilialListSerializer
from finance.models import ExchangeRate
from users.serializers import UserViewListSerializer


class ExchangeRateListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    updated_by_detail = UserViewListSerializer(source='updated_by', read_only=True)

    class Meta:
        model = ExchangeRate
        fields = ('id', 'dollar', 'filial', 'filial_detail', 'updated_time', 'updated_by', 'updated_by_detail')


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ('id', 'dollar', 'filial')