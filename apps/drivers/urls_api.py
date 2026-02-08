from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("drivers", views.DriverViewSet, basename="driver")
router.register("carriers", views.ExternalCarrierViewSet, basename="carrier")

app_name = "drivers"

urlpatterns = [
    path("", include(router.urls)),
]
