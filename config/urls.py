from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/v1/auth/", include("apps.accounts.urls_api")),
    path("api/v1/", include("apps.customers.urls_api")),
    path("api/v1/", include("apps.drivers.urls_api")),
    path("api/v1/", include("apps.shipments.urls_api")),
    path("api/v1/", include("apps.pod.urls_api")),
    path("api/v1/", include("apps.tracking.urls_api")),
    path("api/v1/", include("apps.reports.urls_api")),
    # Tracking pubblico
    path("t/", include("apps.tracking.urls")),
    # QR code redirect
    path("qr/", include("apps.pod.urls_qr")),
    # PWA corriere
    path("pwa/", include("apps.pod.urls_pwa")),
    # Backoffice
    path("", include("apps.backoffice.urls")),
    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
