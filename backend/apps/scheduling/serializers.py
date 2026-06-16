from rest_framework import serializers
from .models import Timetable, TimetableEntry, TimeSlot, RoomBooking


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta: model = TimeSlot; fields = "__all__"


class TimetableEntrySerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    lecturer_name = serializers.CharField(source="lecturer.__str__", read_only=True)
    room_code = serializers.CharField(source="room.code", read_only=True)
    time_slot_label = serializers.CharField(source="time_slot.__str__", read_only=True)
    day_label = serializers.CharField(source="get_day_display", read_only=True)
    group_names = serializers.SerializerMethodField()

    class Meta: model = TimetableEntry; fields = "__all__"

    def get_group_names(self, obj):
        return [str(g) for g in obj.student_groups.all()]


class TimetableSerializer(serializers.ModelSerializer):
    entries = TimetableEntrySerializer(many=True, read_only=True)
    entry_count = serializers.IntegerField(source="entries.count", read_only=True)
    semester_name = serializers.CharField(source="semester.__str__", read_only=True)

    class Meta: model = Timetable; fields = "__all__"


class TimetableListSerializer(serializers.ModelSerializer):
    """Lightweight list view (no entries)."""
    entry_count = serializers.IntegerField(source="entries.count", read_only=True)
    semester_name = serializers.CharField(source="semester.__str__", read_only=True)
    class Meta: model = Timetable; exclude = ()


class RoomBookingSerializer(serializers.ModelSerializer):
    class Meta: model = RoomBooking; fields = "__all__"
