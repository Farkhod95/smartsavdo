from django.urls import re_path, path

from reports.views.debtors import FilialDebtorsReportView
from reports.views.filial_dashboard_reports import FilialDashboardReportView
from reports.views.filial_statistics import FilialSatisticsReportView
from reports.views.order_debt_history import FiliaOrderDebtHistoryReportView
from reports.views.orders_and_debts_report import OrdersAndDebtsReportView
from reports.views.sold_product_history import SoldProductsHistoryView
from reports.views.sold_product_history_detail import SoldProductsHistoryDetailView
from reports.views.sold_product_history_detail_view import ReportOrderHistoryDetailView
from reports.views.top_client import FilialTopClientReportView

urlpatterns = [
    path("reports/filial-dashboard", FilialDashboardReportView.as_view(), name="filial_dashboard_report"),
    path("reports/filial-statistics", FilialSatisticsReportView.as_view(), name="filial_statistics_report"),
    path("reports/debtors", FilialDebtorsReportView.as_view(), name="filial_debtors_report"),
    path("reports/top-client", FilialTopClientReportView.as_view(), name="filial_top_client_report"),
    path("reports/order-debt-history", FiliaOrderDebtHistoryReportView.as_view(), name="filial_order_debt_history_report"),
    path("reports/sold-products-history", SoldProductsHistoryView.as_view(), name="sold-products-history"),
    path("reports/sold-products-history-detail", SoldProductsHistoryDetailView.as_view(), name="sold-products-history-detail"),
    # path("reports/sold-products-history-detail-view/<int:pk>", ReportOrderHistoryDetailView.as_view(), name="sold-products-history-detail-view"),
    path("reports/orders-and-debts-report", OrdersAndDebtsReportView.as_view(), name="orders-and-debts-report"),
]