import os
import pandas as pd

from django.conf import settings
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

# Import models from other apps for auto-seeding
from apps.facilities.models import Room
from apps.staff.models import Lecturer
from apps.academics.models import Programme, StudentGroup, Course, AcademicYear, Semester

from .importer import parse_draft_timetable
from .models import RoomBooking, TimeSlot, Timetable, TimetableEntry, TimetableStatus
from .serializers import (
    RoomBookingSerializer,
    TimeSlotSerializer,
    TimetableEntrySerializer,
    TimetableListSerializer,
    TimetableSerializer,
)


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated]


class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.select_related("semester").all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["semester", "status"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return TimetableListSerializer
        return TimetableSerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        tt = self.get_object()
        tt.status = TimetableStatus.GENERATING
        tt.generated_by = request.user
        tt.save(update_fields=["status", "generated_by"])
        return Response(TimetableSerializer(tt).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        tt = self.get_object()
        tt.status = TimetableStatus.PUBLISHED
        tt.save(update_fields=["status"])
        return Response(TimetableSerializer(tt).data)


class TimetableEntryViewSet(viewsets.ModelViewSet):
    queryset = TimetableEntry.objects.select_related("course", "lecturer", "room", "time_slot").all()
    serializer_class = TimetableEntrySerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["timetable", "day", "lecturer", "room", "course"]


class RoomBookingViewSet(viewsets.ModelViewSet):
    queryset = RoomBooking.objects.all()
    serializer_class = RoomBookingSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["room", "date", "approved"]


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def upload_draft_timetable(request):
    """
    Uploads a draft timetable Excel file, parses it, detects clashes,
    and returns a structured report.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    temp_path = os.path.join(settings.MEDIA_ROOT, "temp_draft.xlsx")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    
    with open(temp_path, "wb+") as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)

    try:
        result = parse_draft_timetable(temp_path)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def auto_seed_from_excel(request):
    """
    Reads the uploaded Excel file and automatically populates the database 
    with missing Rooms, Lecturers, Programmes, Student Groups, and Courses.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        df = pd.read_excel(file_obj, sheet_name="Time Table")
    except Exception as e:
        return Response({"error": f"Failed to read Excel: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure we have a default Academic Year and Semester
    acad_year, _ = AcademicYear.objects.get_or_create(name="2026/2027", defaults={"is_active": True})
    semester, _ = Semester.objects.get_or_create(academic_year=acad_year, number=1, defaults={"name": "Semester 1"})

    stats = {"rooms": 0, "lecturers": 0, "programmes": 0, "groups": 0, "courses": 0}
    
    # Track what we've already created in this loop to avoid hitting the DB repeatedly
    created_rooms = set()
    created_lecturers = set()
    created_programmes = set()
    created_groups = set()
    created_courses = set()

    with transaction.atomic():
        for index, row in df.iterrows():
            # 1. Create Rooms
            room_code = str(row.get("ROOMCODE")).strip() if pd.notna(row.get("ROOMCODE")) else None
            capacity = int(row.get("CAPACITY")) if pd.notna(row.get("CAPACITY")) else 50
            
            if room_code and room_code.upper() not in ["NAN", "NONE", "", "ONLINE"]:
                if room_code not in created_rooms:
                    Room.objects.get_or_create(code=room_code, defaults={"capacity": capacity, "is_physical": True})
                    created_rooms.add(room_code)
                    stats["rooms"] += 1

            # 2. Create Lecturers
            faculty_name = str(row.get("Faculty")).strip() if pd.notna(row.get("Faculty")) else None
            if faculty_name and faculty_name.upper() not in ["X", "TBA", "NAN", "NONE", ""]:
                clean_name = faculty_name.title()
                if clean_name not in created_lecturers:
                    Lecturer.objects.get_or_create(name=clean_name, defaults={"name": clean_name})
                    created_lecturers.add(clean_name)
                    stats["lecturers"] += 1

            # 3. Create Programmes
            prog_code = str(row.get("Programm")).strip() if pd.notna(row.get("Programm")) else None
            if prog_code and prog_code.upper() not in ["NAN", "NONE", ""]:
                if prog_code not in created_programmes:
                    Programme.objects.get_or_create(code=prog_code, defaults={"name": prog_code, "total_semesters": 8})
                    created_programmes.add(prog_code)
                    stats["programmes"] += 1

            # 4. Create Student Groups
            batch_code = str(row.get("BATCHCODE")).strip() if pd.notna(row.get("BATCHCODE")) else None
            if batch_code and batch_code.upper() not in ["NAN", "NONE", ""]:
                prog_obj = Programme.objects.filter(code=prog_code).first() if prog_code else None
                if batch_code not in created_groups:
                    StudentGroup.objects.get_or_create(
                        code=batch_code, 
                        defaults={
                            "programme": prog_obj, 
                            "semester": semester,
                            "head_count": int(row.get("Head Count", 30)) if pd.notna(row.get("Head Count")) else 30
                        }
                    )
                    created_groups.add(batch_code)
                    stats["groups"] += 1

            # 5. Create Courses
            unit_code = str(row.get("UNITCODE")).strip() if pd.notna(row.get("UNITCODE")) else None
            unit_name = str(row.get("UNITNAME")).strip() if pd.notna(row.get("UNITNAME")) else unit_code
            
            if unit_code and unit_code.upper() not in ["NAN", "NONE", ""]:
                prog_obj = Programme.objects.filter(code=prog_code).first() if prog_code else None
                if unit_code not in created_courses:
                    Course.objects.get_or_create(
                        code=unit_code, 
                        defaults={
                            "name": unit_name, 
                            "programme": prog_obj,
                            "semester": semester,
                            "hours_per_week": int(row.get("Hours", 2)) if pd.notna(row.get("Hours")) else 2
                        }
                    )
                    created_courses.add(unit_code)
                    stats["courses"] += 1

    return Response({
        "success": True, 
        "message": "Database auto-seeded successfully!",
        "stats": stats
    })