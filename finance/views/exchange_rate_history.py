from rest_framework import serializers
from finance.models import ExchangeRateHistory
from finance.serializer.exchange_rate_history import ExchangeRateListSerializer, FilialListSerializer  # sizdagi joyiga moslang


class ExchangeRateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRateHistory
        fields = ('id', 'exchange_rate', 'old_dollar', 'new_dollar', 'filial')
        extra_kwargs = {
            'exchange_rate': {"required": True},
            'old_dollar': {"required": True},
            'new_dollar': {"required": True},
            'filial': {"required": False, "allow_null": True},
        }


class ExchangeRateHistoryListSerializer(serializers.ModelSerializer):
    exchange_rate_detail = ExchangeRateListSerializer(source='exchange_rate', read_only=True)
    filial_detail = FilialListSerializer(source='filial', read_only=True)

    class Meta:
        model = ExchangeRateHistory
        fields = ('id', 'exchange_rate', 'exchange_rate_detail', 'old_dollar', 'new_dollar', 'filial', 'filial_detail')