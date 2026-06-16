from rest_framework.routers import DefaultRouter
from .views import TimetableViewSet, TimetableEntryViewSet, TimeSlotViewSet, RoomBookingViewSet

router = DefaultRouter()
router.register("timetables", TimetableViewSet)
router.register("timetable-entries", TimetableEntryViewSet)
router.register("time-slots", TimeSlotViewSet)
router.register("room-bookings", RoomBookingViewSet)
urlpatterns = router.urls
