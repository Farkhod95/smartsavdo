from rest_framework import serializers

from accounts.serializers import FilialListSerializer
from finance.models import Expense
from finance.serializer.expense_category import ExpenseCategoryListSerializer
from users.serializers import UserViewListSerializer


class ExpenseListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    category_detail = ExpenseCategoryListSerializer(source='category', read_only=True)
    employee_detail = UserViewListSerializer(source='employee', read_only=True)

    class Meta:
        model = Expense
        fields = ('id', 'filial', 'filial_detail', 'category', 'category_detail', 'is_salary', 'employee', 'employee_detail', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete')


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ('id', 'filial', 'category', 'is_salary', 'employee', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
                  'summa_terminal', 'summa_transfer', 'date', 'note', 'is_delete')