from rest_framework import serializers
from .models import Room, Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta: model = Equipment; fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    equipment_codes = serializers.SerializerMethodField()
    class Meta: model = Room; fields = "__all__"
    def get_equipment_codes(self, obj):
        return list(obj.equipment.values_list("code", flat=True))
