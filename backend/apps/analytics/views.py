from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, F, Q
from apps.scheduling.models import TimetableEntry, Timetable
from apps.staff.models import Lecturer, LecturerRank
from apps.facilities.models import Room


def _hours_for_entry(e):
    # each slot ~ 2 hours by convention
    return 2


class WorkloadReportView(APIView):
    def get(self, request):
        timetable_id = request.query_params.get("timetable")
        qs = TimetableEntry.objects.all()
        if timetable_id:
            qs = qs.filter(timetable_id=timetable_id)
        rows = []
        for lec in Lecturer.objects.select_related("user", "department").all():
            n = qs.filter(lecturer=lec).count()
            hours = n * 2
            cap = LecturerRank.max_hours(lec.rank)
            rows.append({
                "lecturer_id": lec.id,
                "name": str(lec),
                "rank": lec.rank,
                "department": lec.department.name,
                "hours": hours,
                "max_hours": cap,
                "utilization": round(hours / cap * 100, 1) if cap else 0,
                "overloaded": hours > cap,
            })
        return Response(rows)


class RoomUtilizationView(APIView):
    def get(self, request):
        timetable_id = request.query_params.get("timetable")
        qs = TimetableEntry.objects.all()
        if timetable_id:
            qs = qs.filter(timetable_id=timetable_id)
        # 5 weekdays * 4 slots = 20 slots/week; PG saturday adds 4
        max_slots = 20
        rows = []
        for r in Room.objects.filter(is_active=True):
            used = qs.filter(room=r).count()
            rows.append({
                "room_id": r.id, "code": r.code, "type": r.room_type,
                "capacity": r.capacity, "sessions": used,
                "utilization": round(used / max_slots * 100, 1),
            })
        return Response(rows)


class ClashReportView(APIView):
    def get(self, request):
        timetable_id = request.query_params.get("timetable")
        qs = TimetableEntry.objects.all()
        if timetable_id:
            qs = qs.filter(timetable_id=timetable_id)
        room_clashes = (
            qs.values("day", "time_slot", "room")
              .annotate(c=Count("id")).filter(c__gt=1)
        )
        lect_clashes = (
            qs.values("day", "time_slot", "lecturer")
              .annotate(c=Count("id")).filter(c__gt=1)
        )
        return Response({
            "room_clashes": list(room_clashes),
            "lecturer_clashes": list(lect_clashes),
        })


class StudentDaysReportView(APIView):
    def get(self, request):
        timetable_id = request.query_params.get("timetable")
        qs = TimetableEntry.objects.all()
        if timetable_id:
            qs = qs.filter(timetable_id=timetable_id)
        # Days per group
        from apps.academics.models import StudentGroup
        rows = []
        for g in StudentGroup.objects.all():
            entries = qs.filter(student_groups=g)
            days = sorted(set(entries.values_list("day", flat=True)))
            rows.append({
                "group_id": g.id, "name": str(g),
                "days": days, "day_count": len(days), "sessions": entries.count(),
            })
        return Response(rows)


class DashboardStatsView(APIView):
    def get(self, request):
        from apps.academics.models import Faculty, Department, Programme, Course, StudentGroup
        return Response({
            "faculties": Faculty.objects.count(),
            "departments": Department.objects.count(),
            "programmes": Programme.objects.count(),
            "courses": Course.objects.count(),
            "lecturers": Lecturer.objects.count(),
            "rooms": Room.objects.count(),
            "student_groups": StudentGroup.objects.count(),
            "timetables": Timetable.objects.count(),
            "published_timetables": Timetable.objects.filter(status="PUBLISHED").count(),
        })
