from django.urls import re_path, path

from finance.views.debt_repayment import DebtRepaymentView, DebtRepaymentDetailView, DebtRepaymentFieldInfoView, \
    DebtRepaymentKarzinkaView, DebtRepaymentDetailKarzinkaView, DebtRepaymentGroupedByDateView, \
    DebtRepaymentRestoreKarzinkaView
from finance.views.exchange_rate import ExchangeRateView, ExchangeRateDetailView, ExchangeRateFieldInfoView
from finance.views.exchange_rate_history import ExchangeRateHistoryView, ExchangeRateHistoryDetailView, \
    ExchangeRateHistoryFieldInfoView
from finance.views.expense import ExpenseView, ExpenseDetailView, ExpenseFieldInfoView, ExpenseGroupByDateView
from finance.views.expense_category import ExpenseCategoryView, ExpenseCategoryDetailView, ExpenseCategoryFieldInfoView

urlpatterns = [
    re_path(r'^exchange-rate$', ExchangeRateView.as_view(), name='exchange_rate_view'),
    path('exchange-rate/<int:pk>', ExchangeRateDetailView.as_view(), name='exchange_rate_detail_view'),
    path('exchange-rate/fields', ExchangeRateFieldInfoView.as_view(), name='exchange_rate_fields_info'),

    re_path(r'^exchange-rate-history/$', ExchangeRateHistoryView.as_view(), name='exchange_rate_history_view'),
    path('exchange-rate-history/<int:pk>', ExchangeRateHistoryDetailView.as_view(), name='exchange_rate_history_detail_view'),
    path('exchange-rate-history/fields/', ExchangeRateHistoryFieldInfoView.as_view(), name='exchange_rate_history_fields_info'),

    re_path(r'^expense-category$', ExpenseCategoryView.as_view(), name='expense_category_view'),
    path('expense-category/<int:pk>', ExpenseCategoryDetailView.as_view(), name='expense_category_detail_view'),
    path('expense-category/fields', ExpenseCategoryFieldInfoView.as_view(), name='expense_category_fields_info'),

    re_path(r'^expense$', ExpenseView.as_view(), name='expense_view'),
    path('expense/group-by-date', ExpenseGroupByDateView.as_view(), name='expense_group_by_date_view'),
    path('expense/<int:pk>', ExpenseDetailView.as_view(), name='expense_detail_view'),
    path('expense/fields', ExpenseFieldInfoView.as_view(), name='expense_fields_info'),

    re_path(r'^debt-repayment$', DebtRepaymentView.as_view(), name='debt_repayment_view'),
    path('debt-repayment/grouped-by-date', DebtRepaymentGroupedByDateView.as_view(), name='debt_repayment_grouped_by_date'),
    path('debt-repayment/<int:pk>', DebtRepaymentDetailView.as_view(), name='debt_repayment_detail_view'),
    path('debt-repayment/karzinka', DebtRepaymentKarzinkaView.as_view(), name='debt_repayment_karzinka_view'),
    path('debt-repayment/karzinka/<int:pk>/restore', DebtRepaymentRestoreKarzinkaView.as_view(),
         name='debt_repayment_karzinka_restore'),
    path('debt-repayment/karzinka/<int:pk>', DebtRepaymentDetailKarzinkaView.as_view(),
         name='debt_repayment_karzinka_detail_view'),
    path('debt-repayment/fields', DebtRepaymentFieldInfoView.as_view(), name='debt_repayment_fields_info'),
]