from rest_framework import serializers
from .models import (
    Faculty, Department, Programme, Semester, Term, Course,
    StudentGroup, AcademicYear, Holiday,
)


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta: model = AcademicYear; fields = "__all__"


class FacultySerializer(serializers.ModelSerializer):
    departments_count = serializers.IntegerField(source="departments.count", read_only=True)
    class Meta: model = Faculty; fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source="faculty.name", read_only=True)
    programmes_count = serializers.IntegerField(source="programmes.count", read_only=True)
    class Meta: model = Department; fields = "__all__"


class ProgrammeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    courses_count = serializers.IntegerField(source="courses.count", read_only=True)
    class Meta: model = Programme; fields = "__all__"


class SemesterSerializer(serializers.ModelSerializer):
    class Meta: model = Semester; fields = "__all__"


class TermSerializer(serializers.ModelSerializer):
    class Meta: model = Term; fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    programme_code = serializers.CharField(source="programme.code", read_only=True)
    class Meta: model = Course; fields = "__all__"


class StudentGroupSerializer(serializers.ModelSerializer):
    programme_code = serializers.CharField(source="programme.code", read_only=True)
    class Meta: model = StudentGroup; fields = "__all__"


class HolidaySerializer(serializers.ModelSerializer):
    class Meta: model = Holiday; fields = "__all__"
