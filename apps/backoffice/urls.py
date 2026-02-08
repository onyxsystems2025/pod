from django.urls import path

from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("shipments/", views.ShipmentListView.as_view(), name="shipment-list"),
    path("shipments/create/", views.ShipmentCreateView.as_view(), name="shipment-create"),
    path("shipments/<uuid:uuid>/", views.ShipmentDetailView.as_view(), name="shipment-detail"),
    path(
        "shipments/<uuid:uuid>/transition/",
        views.ShipmentTransitionView.as_view(),
        name="shipment-transition",
    ),
    path("customers/", views.CustomerListView.as_view(), name="customer-list"),
]
