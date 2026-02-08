from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:shipment_uuid>/", views.QRCodeRedirectView.as_view(), name="qr-redirect"),
]
