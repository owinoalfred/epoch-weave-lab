from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/timetables/", include("apps.scheduling.urls")),
    path("api/time-slots/", include("apps.scheduling.urls")),  # If you have separate urls
    path("api/academics/", include("apps.academics.urls")),
    path("api/staff/", include("apps.staff.urls")),
    path("api/facilities/", include("apps.facilities.urls")),
    path("api/optimization/", include("apps.optimization.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)