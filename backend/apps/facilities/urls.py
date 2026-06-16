from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, EquipmentViewSet

router = DefaultRouter()
router.register("rooms", RoomViewSet)
router.register("equipment", EquipmentViewSet)
urlpatterns = router.urls
