from rest_framework import serializers

from finance.models import ExpenseCategory


class ExpenseCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'name')


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'name')