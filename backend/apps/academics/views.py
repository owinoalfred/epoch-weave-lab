from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Faculty, Department, Programme, Semester, Term, Course,
    StudentGroup, AcademicYear, Holiday,
)
from .serializers import (
    FacultySerializer, DepartmentSerializer, ProgrammeSerializer,
    SemesterSerializer, TermSerializer, CourseSerializer,
    StudentGroupSerializer, AcademicYearSerializer, HolidaySerializer,
)


class _Base(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


class AcademicYearViewSet(_Base):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    search_fields = ["name"]


class FacultyViewSet(_Base):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    search_fields = ["name", "code"]


class DepartmentViewSet(_Base):
    queryset = Department.objects.select_related("faculty").all()
    serializer_class = DepartmentSerializer
    filterset_fields = ["faculty"]
    search_fields = ["name", "code"]


class ProgrammeViewSet(_Base):
    queryset = Programme.objects.select_related("department").all()
    serializer_class = ProgrammeSerializer
    filterset_fields = ["department", "level"]
    search_fields = ["name", "code"]


class SemesterViewSet(_Base):
    queryset = Semester.objects.select_related("academic_year").all()
    serializer_class = SemesterSerializer
    filterset_fields = ["academic_year", "is_active"]


class TermViewSet(_Base):
    queryset = Term.objects.select_related("semester").all()
    serializer_class = TermSerializer
    filterset_fields = ["semester"]


class CourseViewSet(_Base):
    queryset = Course.objects.select_related("programme").all()
    serializer_class = CourseSerializer
    filterset_fields = ["programme", "year_of_study", "semester_number", "has_lab"]
    search_fields = ["code", "title"]


class StudentGroupViewSet(_Base):
    queryset = StudentGroup.objects.select_related("programme").all()
    serializer_class = StudentGroupSerializer
    filterset_fields = ["programme", "year_of_study"]
    search_fields = ["name"]


class HolidayViewSet(_Base):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
