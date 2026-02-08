from django.urls import path

from . import views

app_name = "tracking"

urlpatterns = [
    path("tracking/<str:token>/", views.TrackingAPIView.as_view(), name="tracking-api"),
]
