from rest_framework import serializers
from finance.models import ExchangeRateHistory
from finance.serializer.exchange_rate import ExchangeRateListSerializer, FilialListSerializer  # sizdagi joyiga moslang
from users.serializers import UserViewListSerializer


class ExchangeRateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRateHistory
        fields = (
            'id',
            'exchange_rate',
            'old_dollar',
            'new_dollar',
            'filial',
            'created_time',
            'created_by',
        )
        read_only_fields = ('id', 'created_time', 'created_by')


class ExchangeRateHistoryListSerializer(serializers.ModelSerializer):
    exchange_rate_detail = ExchangeRateListSerializer(source='exchange_rate', read_only=True)
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    created_by_detail = UserViewListSerializer(source='created_by', read_only=True)

    class Meta:
        model = ExchangeRateHistory
        fields = ('id', 'exchange_rate', 'exchange_rate_detail', 'old_dollar', 'new_dollar', 'filial', 'filial_detail', 'created_time', 'created_by', 'created_by_detail')