from django.urls import path
from .views import trigger_solver

urlpatterns = [
    path("timetable/generate/", trigger_solver, name="generate-timetable"),
]