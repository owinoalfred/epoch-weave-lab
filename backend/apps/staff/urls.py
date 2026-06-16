from rest_framework.routers import DefaultRouter
from .views import LecturerViewSet, CourseAllocationViewSet

router = DefaultRouter()
router.register("lecturers", LecturerViewSet)
router.register("course-allocations", CourseAllocationViewSet)
urlpatterns = router.urls
