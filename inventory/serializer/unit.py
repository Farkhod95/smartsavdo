from rest_framework import serializers
from inventory.models import Unit


class UnitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ('id', 'code', 'name', 'is_active')


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ('id', 'code', 'name', 'is_active')