from rest_framework import serializers
from sales.models import ClientKeshbekHistory
from sales.serializer.client import ClientListSerializer


class ClientKeshbekHistoryListSerializer(serializers.ModelSerializer):
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = ClientKeshbekHistory
        fields = ('id', 'client', 'client_detail', 'keshbek', 'keshbek_summa', 'order_history')


class ClientKeshbekHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientKeshbekHistory
        fields = ('id', 'client', 'keshbek', 'keshbek_summa', 'order_history')