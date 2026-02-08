from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("dashboard/stats/", views.DashboardStatsView.as_view(), name="dashboard-stats"),
    path("reports/export/csv/", views.DeliveriesExportCSVView.as_view(), name="export-csv"),
]
