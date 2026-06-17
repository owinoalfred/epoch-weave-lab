from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Timetable, TimetableEntry, TimeSlot, RoomBooking, TimetableStatus
from .serializers import (
    TimetableSerializer, TimetableListSerializer, TimetableEntrySerializer,
    TimeSlotSerializer, RoomBookingSerializer,
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