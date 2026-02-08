from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("customers", views.CustomerViewSet, basename="customer")

app_name = "customers"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "customers/<uuid:customer_uuid>/addresses/",
        views.AddressViewSet.as_view({"get": "list", "post": "create"}),
        name="customer-addresses",
    ),
    path(
        "customers/<uuid:customer_uuid>/addresses/<uuid:uuid>/",
        views.AddressViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="customer-address-detail",
    ),
]
