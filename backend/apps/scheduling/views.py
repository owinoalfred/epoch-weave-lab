import os

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
    queryset = Timetable.objects.select_related("semester", "department").all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["semester", "department", "status"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return TimetableListSerializer
        return TimetableSerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """Start the generation process. (Celery task will be hooked here in Phase 2)"""
        tt = self.get_object()
        tt.status = TimetableStatus.GENERATING
        tt.generated_by = request.user
        tt.save(update_fields=["status", "generated_by"])
        
        # TODO: Trigger Celery task for OR-Tools solver here
        # For now, we just mark it as generating.
        
        return Response(TimetableSerializer(tt).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish the timetable."""
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
def upload_draft_timetable(request):
    """
    Uploads a draft timetable Excel file, parses it, detects clashes,
    and returns a structured report. Does NOT save to DB yet.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    # Save temporarily
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
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)