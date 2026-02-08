from django.urls import path

from . import views

app_name = "pod"

urlpatterns = [
    path(
        "driver/shipments/<uuid:shipment_uuid>/pod/",
        views.PODCreateView.as_view(),
        name="pod-create",
    ),
    path("pod/<uuid:uuid>/", views.PODDetailView.as_view(), name="pod-detail"),
    path(
        "pod/<uuid:pod_uuid>/photos/",
        views.PODPhotoUploadView.as_view(),
        name="pod-photo-upload",
    ),
    path("pod/sync/", views.PODSyncView.as_view(), name="pod-sync"),
]
