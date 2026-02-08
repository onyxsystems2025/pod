from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("shipments", views.ShipmentViewSet, basename="shipment")

driver_router = DefaultRouter()
driver_router.register("driver/shipments", views.DriverShipmentViewSet, basename="driver-shipment")

app_name = "shipments"

urlpatterns = [
    path("", include(router.urls)),
    path("", include(driver_router.urls)),
]
