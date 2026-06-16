from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Room, Equipment
from .serializers import RoomSerializer, EquipmentSerializer


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code"]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.prefetch_related("equipment").all()
    serializer_class = RoomSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["room_type", "building", "is_active"]
    search_fields = ["code", "name", "building"]
    ordering_fields = ["capacity", "code"]
