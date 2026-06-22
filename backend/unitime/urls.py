from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Auth
    path("api/auth/", include("apps.accounts.urls")),
    
    # Scheduling & Timetables
    path("api/timetables/", include("apps.scheduling.urls")),
    path("api/time-slots/", include("apps.scheduling.urls")),
    
    # Academics & Facilities (Adding aliases for /api/rooms and /api/faculties)
    path("api/academics/", include("apps.academics.urls")),
    path("api/faculties/", include("apps.academics.urls")), # Alias for frontend
    path("api/staff/", include("apps.staff.urls")),
    path("api/facilities/", include("apps.facilities.urls")),
    path("api/rooms/", include("apps.facilities.urls")), # Alias for frontend
    
    # Optimization & Analytics
    path("api/optimization/", include("apps.optimization.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)