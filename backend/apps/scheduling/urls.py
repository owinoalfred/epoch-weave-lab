from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TimetableViewSet, 
    TimetableEntryViewSet, 
    TimeSlotViewSet, 
    RoomBookingViewSet,
    upload_draft_timetable,
    auto_seed_from_excel
)

router = DefaultRouter()
router.register(r'timetables', TimetableViewSet)
router.register(r'timetable-entries', TimetableEntryViewSet)
router.register(r'time-slots', TimeSlotViewSet)
router.register(r'room-bookings', RoomBookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('import/draft/', upload_draft_timetable, name='import-draft'),
    path('auto-seed/', auto_seed_from_excel, name='auto-seed'),
]