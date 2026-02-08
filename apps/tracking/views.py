from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework import permissions, serializers
from rest_framework.generics import RetrieveAPIView

from apps.shipments.models import Shipment


class TrackingPageView(TemplateView):
    template_name = "tracking/tracking_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs["token"]
        shipment = get_object_or_404(
            Shipment.objects.select_related(
                "sender", "external_carrier",
            ).prefetch_related("events"),
            public_tracking_token=token,
        )
        context["shipment"] = shipment
        context["events"] = shipment.events.all()

        # POD data se consegnata
        pod = None
        if hasattr(shipment, "pod"):
            try:
                pod = shipment.pod
            except Exception:
                pass
        context["pod"] = pod
        context["pod_photos"] = pod.photos.all() if pod else []

        return context


class TrackingAPISerializer(serializers.Serializer):
    tracking_code = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.SerializerMethodField()
    recipient_name = serializers.CharField()
    sender_name = serializers.SerializerMethodField()
    delivery_address = serializers.SerializerMethodField()
    estimated_delivery_date = serializers.DateField()
    actual_delivery_date = serializers.DateTimeField()
    external_tracking_url = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    pod = serializers.SerializerMethodField()

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_sender_name(self, obj):
        return obj.sender.company_name

    def get_delivery_address(self, obj):
        return obj.get_effective_delivery_address()

    def get_external_tracking_url(self, obj):
        return obj.get_external_tracking_url()

    def get_events(self, obj):
        return [
            {
                "status": e.get_status_display(),
                "description": e.description,
                "location": e.location,
                "timestamp": e.created_at.isoformat(),
            }
            for e in obj.events.all()
        ]

    def get_pod(self, obj):
        try:
            pod = obj.pod
        except Exception:
            return None
        return {
            "delivery_result": pod.get_delivery_result_display(),
            "recipient_signer_name": pod.recipient_signer_name,
            "recorded_at": pod.recorded_at.isoformat(),
            "has_signature": bool(pod.signature_image),
            "photos_count": pod.photos.count(),
        }


class TrackingAPIView(RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TrackingAPISerializer
    lookup_field = "public_tracking_token"
    lookup_url_kwarg = "token"

    def get_queryset(self):
        return Shipment.objects.select_related(
            "sender", "external_carrier",
        ).prefetch_related("events")
