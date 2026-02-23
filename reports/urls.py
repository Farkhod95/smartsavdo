from django.urls import re_path, path

from reports.views.filial_dashboard_reports import FilialDashboardReportView

urlpatterns = [
    path("reports/filial-dashboard", FilialDashboardReportView.as_view(), name="filial_dashboard_report"),
]