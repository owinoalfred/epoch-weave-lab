from django.urls import path
from .views import (
    WorkloadReportView, RoomUtilizationView, ClashReportView,
    StudentDaysReportView, DashboardStatsView,
)

urlpatterns = [
    path("reports/workloads", WorkloadReportView.as_view()),
    path("reports/room-utilization", RoomUtilizationView.as_view()),
    path("reports/clashes", ClashReportView.as_view()),
    path("reports/student-days", StudentDaysReportView.as_view()),
    path("reports/dashboard", DashboardStatsView.as_view()),
]
