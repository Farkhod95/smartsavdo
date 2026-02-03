from django.urls import re_path, path

from finance.views.debt_repayment import DebtRepaymentView, DebtRepaymentDetailView, DebtRepaymentFieldInfoView
from finance.views.exchange_rate import ExchangeRateView, ExchangeRateDetailView, ExchangeRateFieldInfoView
from finance.views.expense import ExpenseView, ExpenseDetailView, ExpenseFieldInfoView
from finance.views.expense_category import ExpenseCategoryView, ExpenseCategoryDetailView, ExpenseCategoryFieldInfoView

urlpatterns = [
    re_path(r'^exchange-rate$', ExchangeRateView.as_view(), name='exchange_rate_view'),
    path('exchange-rate/<int:pk>', ExchangeRateDetailView.as_view(), name='exchange_rate_detail_view'),
    path('exchange-rate/fields', ExchangeRateFieldInfoView.as_view(), name='exchange_rate_fields_info'),

    re_path(r'^expense-category$', ExpenseCategoryView.as_view(), name='expense_category_view'),
    path('expense-category/<int:pk>', ExpenseCategoryDetailView.as_view(), name='expense_category_detail_view'),
    path('expense-category/fields', ExpenseCategoryFieldInfoView.as_view(), name='expense_category_fields_info'),

    re_path(r'^expense$', ExpenseView.as_view(), name='expense_view'),
    path('expense/<int:pk>', ExpenseDetailView.as_view(), name='expense_detail_view'),
    path('expense/fields/', ExpenseFieldInfoView.as_view(), name='expense_fields_info'),

    re_path(r'^debt-repayment$', DebtRepaymentView.as_view(), name='debt_repayment_view'),
    path('debt-repayment/<int:pk>', DebtRepaymentDetailView.as_view(), name='debt_repayment_detail_view'),
    path('debt-repayment/fields/', DebtRepaymentFieldInfoView.as_view(), name='debt_repayment_fields_info'),
]