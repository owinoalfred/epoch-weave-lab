from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.academics.urls")),
    path("api/", include("apps.facilities.urls")),
    path("api/", include("apps.staff.urls")),
    path("api/", include("apps.scheduling.urls")),
    path("api/", include("apps.optimization.urls")),
    path("api/", include("apps.analytics.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]
