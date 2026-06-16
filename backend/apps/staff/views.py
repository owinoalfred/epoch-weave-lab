from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Lecturer, CourseAllocation
from .serializers import LecturerSerializer, CourseAllocationSerializer


class LecturerViewSet(viewsets.ModelViewSet):
    queryset = Lecturer.objects.select_related("user", "department").all()
    serializer_class = LecturerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["department", "rank", "is_active"]
    search_fields = ["staff_no", "user__first_name", "user__last_name", "user__email"]


class CourseAllocationViewSet(viewsets.ModelViewSet):
    queryset = CourseAllocation.objects.select_related("lecturer", "course", "semester").all()
    serializer_class = CourseAllocationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lecturer", "course", "semester"]
