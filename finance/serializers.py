from rest_framework import serializers

from accounts.serializers import FilialListSerializer
from finance.models import ExchangeRate, ExpenseCategory, Expense, DebtRepayment
from sales.serializer.client import ClientListSerializer
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


class ExpenseCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'name')


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'name')


class ExpenseListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    category_detail = ExpenseCategoryListSerializer(source='category', read_only=True)

    class Meta:
        model = Expense
        fields = ('id', 'filial', 'filial_detail', 'category', 'category_detail', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete')


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ('id', 'filial', 'category', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete')


class DebtRepaymentListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = DebtRepayment
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'debt_status')


class DebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtRepayment
        fields = ('id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'debt_status')


