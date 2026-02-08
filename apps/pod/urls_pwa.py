from django.urls import path

from . import views

urlpatterns = [
    path("", views.PWAView.as_view(), name="pwa-home"),
    path("pod/<uuid:shipment_uuid>/", views.PWAView.as_view(), name="pwa-pod"),
    path("offline/", views.PWAOfflineView.as_view(), name="pwa-offline"),
]
