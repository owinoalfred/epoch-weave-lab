import os
import re
import pandas as pd
from django.db import transaction
from django.conf import settings
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.academics.models import Programme, Semester, AcademicYear, StudentGroup, Course
from apps.staff.models import Lecturer
from apps.facilities.models import Room

from .models import TimeSlot, Timetable, TimetableEntry, RoomBooking, TimetableStatus
from .serializers import (
    TimeSlotSerializer, TimetableSerializer, TimetableEntrySerializer, 
    RoomBookingSerializer, TimetableListSerializer
)
from .importer import parse_draft_timetable

class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.select_related("semester").all()
    serializer_class = TimetableSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["semester", "status"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list": return TimetableListSerializer
        return TimetableSerializer

class TimetableEntryViewSet(viewsets.ModelViewSet):
    queryset = TimetableEntry.objects.select_related("course", "lecturer", "room", "time_slot").all()
    serializer_class = TimetableEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["timetable", "day", "lecturer", "room", "course"]

class RoomBookingViewSet(viewsets.ModelViewSet):
    queryset = RoomBooking.objects.all()
    serializer_class = RoomBookingSerializer

@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_draft_timetable(request):
    """Uploads Excel, parses it, and returns clashes/warnings."""
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    temp_path = os.path.join(settings.MEDIA_ROOT, "temp_draft.xlsx")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    with open(temp_path, "wb+") as destination:
        for chunk in file_obj.chunks(): destination.write(chunk)

    try:
        result = parse_draft_timetable(temp_path)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@api_view(["POST"])
@parser_classes([MultiPartParser])
def auto_seed_from_excel(request):
    """
    Reads the uploaded Excel file and auto-seeds the database with
    Rooms, Lecturers, Programmes, Student Groups, and Courses.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    temp_path = os.path.join(settings.MEDIA_ROOT, "temp_seed.xlsx")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    with open(temp_path, "wb+") as destination:
        for chunk in file_obj.chunks(): destination.write(chunk)

    try:
        df_tt = pd.read_excel(temp_path, sheet_name="Time Table")
        df_tt.columns = [str(c).strip() for c in df_tt.columns]
        
        stats = {"rooms": 0, "lecturers": 0, "programmes": 0, "groups": 0, "courses": 0}
        
        # Default Academic Year and Semester
        acad_year, _ = AcademicYear.objects.get_or_create(name="2026/2027", defaults={"is_active": True})
        semester, _ = Semester.objects.get_or_create(academic_year=acad_year, number=1, defaults={"name": "Semester 1"})
        
        with transaction.atomic():
            # 1. Seed Rooms (from Room Capacity sheet & Time Table)
            try:
                df_rooms = pd.read_excel(temp_path, sheet_name="Room Capacity", header=None)
                for index, row in df_rooms.iterrows():
                    col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                    col1 = row.iloc[1] if pd.notna(row.iloc[1]) else 50
                    if re.match(r'^([A-Z]?\d{3})$', col0):
                        capacity = int(col1) if isinstance(col1, (int, float)) else 50
                        _, created = Room.objects.get_or_create(code=col0, defaults={"capacity": capacity, "is_physical": True})
                        if created: stats["rooms"] += 1
            except Exception as e:
                print(f"Error reading Room Capacity sheet: {e}")
            
            # Also seed rooms from Time Table sheet
            unique_rooms = df_tt['ROOMCODE'].dropna().unique()
            for room_code in unique_rooms:
                room_code = str(room_code).strip()
                if re.match(r'^([A-Z]?\d{3})$', room_code) or room_code.startswith("ONLINE"):
                    _, created = Room.objects.get_or_create(code=room_code, defaults={"capacity": 50, "is_physical": not room_code.startswith("ONLINE")})
                    if created: stats["rooms"] += 1

            # 2. Seed Lecturers
            unique_lecturers = df_tt['Faculty'].dropna().unique()
            for lec_name in unique_lecturers:
                lec_name = str(lec_name).strip()
                if lec_name and lec_name.upper() not in ["X", "NAN", "UNKNOWN", ""]:
                    _, created = Lecturer.objects.get_or_create(name=lec_name, defaults={"name": lec_name})
                    if created: stats["lecturers"] += 1

            # 3. Seed Programmes
            unique_programmes = df_tt['Programm'].dropna().unique()
            prog_map = {}
            for prog_name in unique_programmes:
                prog_name = str(prog_name).strip()
                if prog_name and prog_name.upper() not in ["NAN", ""]:
                    level = "UNDERGRAD"
                    if "MSC" in prog_name.upper() or "PHD" in prog_name.upper(): level = "POSTGRAD"
                    elif "MBA" in prog_name.upper(): level = "MASTERS"
                    
                    obj, created = Programme.objects.get_or_create(
                        code=prog_name, defaults={"name": prog_name, "level": level, "total_semesters": 8}
                    )
                    prog_map[prog_name] = obj
                    if created: stats["programmes"] += 1

            # 4. Seed Student Groups (Batches)
            unique_batches = df_tt['BATCHCODE'].dropna().unique()
            batch_map = {}
            for batch_code in unique_batches:
                batch_code = str(batch_code).strip()
                if batch_code and batch_code.upper() not in ["NAN", ""]:
                    prog_obj = None
                    # Try to match batch code to programme
                    for p_name, p_obj in prog_map.items():
                        if batch_code.startswith(p_name):
                            prog_obj = p_obj
                            break
                    
                    obj, created = StudentGroup.objects.get_or_create(
                        code=batch_code, defaults={"programme": prog_obj, "semester": semester, "head_count": 30}
                    )
                    batch_map[batch_code] = obj
                    if created: stats["groups"] += 1

            # 5. Seed Courses
            unique_courses = df_tt[['UNITCODE', 'UNITNAME']].dropna(subset=['UNITCODE']).drop_duplicates()
            for index, row in unique_courses.iterrows():
                unit_code = str(row['UNITCODE']).strip()
                unit_name = str(row['UNITNAME']).strip() if pd.notna(row['UNITNAME']) else unit_code
                
                if unit_code and unit_code.upper() not in ["NAN", ""]:
                    course_rows = df_tt[df_tt['UNITCODE'] == unit_code]
                    prog_obj = None
                    if not course_rows.empty:
                        prog_name = str(course_rows.iloc[0]['Programm']).strip()
                        prog_obj = prog_map.get(prog_name)
                    
                    _, created = Course.objects.get_or_create(
                        code=unit_code, defaults={"name": unit_name, "programme": prog_obj, "semester": semester, "hours_per_week": 2}
                    )
                    if created: stats["courses"] += 1

        return Response({"success": True, "message": "Database auto-seeded successfully!", "stats": stats}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)