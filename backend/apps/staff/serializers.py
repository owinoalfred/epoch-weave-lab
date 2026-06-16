from rest_framework import serializers
from .models import Lecturer, CourseAllocation, LecturerRank


class LecturerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    max_weekly_hours = serializers.IntegerField(read_only=True)

    class Meta: model = Lecturer; fields = "__all__"
    def get_name(self, obj): return str(obj)


class CourseAllocationSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    lecturer_name = serializers.CharField(source="lecturer.__str__", read_only=True)
    class Meta: model = CourseAllocation; fields = "__all__"
