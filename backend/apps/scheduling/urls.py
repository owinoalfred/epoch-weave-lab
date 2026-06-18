from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TimetableViewSet, 
    TimetableEntryViewSet, 
    TimeSlotViewSet, 
    RoomBookingViewSet,
    upload_draft_timetable
)

router = DefaultRouter()
router.register(r'timetables', TimetableViewSet)
router.register(r'entries', TimetableEntryViewSet)
router.register(r'slots', TimeSlotViewSet)
router.register(r'bookings', RoomBookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Map the Excel upload endpoint
    path('import/draft/', upload_draft_timetable, name='import-draft'),
]