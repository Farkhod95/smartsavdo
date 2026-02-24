from django.urls import re_path, path

from reports.views.filial_dashboard_reports import FilialDashboardReportView
from reports.views.filial_statistics import FilialSatisticsReportView

urlpatterns = [
    path("reports/filial-dashboard", FilialDashboardReportView.as_view(), name="filial_dashboard_report"),
    path("reports/filial-statistics", FilialSatisticsReportView.as_view(), name="filial_statistics_report"),
]