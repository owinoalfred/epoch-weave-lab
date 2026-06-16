from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
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


class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.select_related("semester", "department").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["semester", "department", "status"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return TimetableListSerializer
        return TimetableSerializer

    @action(detail=True, methods=["post"])
    def submit_for_approval(self, request, pk=None):
        tt = self.get_object()
        tt.status = TimetableStatus.READY
        tt.save(update_fields=["status"])
        return Response(TimetableSerializer(tt).data)

    @action(detail=True, methods=["post"])
    def hod_approve(self, request, pk=None):
        tt = self.get_object()
        tt.status = TimetableStatus.HOD_APPROVED
        tt.hod_approved_by = request.user
        tt.save()
        return Response(TimetableSerializer(tt).data)

    @action(detail=True, methods=["post"])
    def dean_approve(self, request, pk=None):
        tt = self.get_object()
        tt.status = TimetableStatus.DEAN_APPROVED
        tt.dean_approved_by = request.user
        tt.save()
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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["timetable", "day", "lecturer", "room", "course"]


class RoomBookingViewSet(viewsets.ModelViewSet):
    queryset = RoomBooking.objects.all()
    serializer_class = RoomBookingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["room", "date", "approved"]
