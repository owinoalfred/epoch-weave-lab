from rest_framework.routers import DefaultRouter
from .views import (
    FacultyViewSet, DepartmentViewSet, ProgrammeViewSet, SemesterViewSet,
    TermViewSet, CourseViewSet, StudentGroupViewSet, AcademicYearViewSet,
    HolidayViewSet,
)

router = DefaultRouter()
router.register("academic-years", AcademicYearViewSet)
router.register("faculties", FacultyViewSet)
router.register("departments", DepartmentViewSet)
router.register("programmes", ProgrammeViewSet)
router.register("semesters", SemesterViewSet)
router.register("terms", TermViewSet)
router.register("courses", CourseViewSet)
router.register("student-groups", StudentGroupViewSet)
router.register("holidays", HolidayViewSet)

urlpatterns = router.urls
