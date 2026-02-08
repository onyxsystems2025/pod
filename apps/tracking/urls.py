from django.urls import path

from . import views

urlpatterns = [
    path("<str:token>/", views.TrackingPageView.as_view(), name="tracking-page"),
]
