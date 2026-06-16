from django.urls import path
from .views import GenerateTimetableView, JobStatusView

urlpatterns = [
    path("timetable/generate", GenerateTimetableView.as_view()),
    path("jobs/<str:task_id>", JobStatusView.as_view()),
]
