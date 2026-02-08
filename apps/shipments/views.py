from django.http import HttpResponse as DjangoHttpResponse
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsDriver, IsOperatorOrAdmin
from apps.drivers.models import Driver, ExternalCarrier

from .models import Shipment, ShipmentEvent
from .serializers import (
    ShipmentAssignSerializer,
    ShipmentCreateSerializer,
    ShipmentDetailSerializer,
    ShipmentEventSerializer,
    ShipmentListSerializer,
    ShipmentTransitionSerializer,
)
from .state_machine import InvalidTransitionError, transition_shipment


class ShipmentFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Shipment.Status.choices)
    delivery_type = filters.ChoiceFilter(choices=Shipment.DeliveryType.choices)
    priority = filters.ChoiceFilter(choices=Shipment.Priority.choices)
    sender = filters.UUIDFilter(field_name="sender__uuid")
    driver = filters.UUIDFilter(field_name="driver__uuid")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    estimated_date = filters.DateFilter(field_name="estimated_delivery_date")

    class Meta:
        model = Shipment
        fields = ["status", "delivery_type", "priority", "sender", "driver"]


class ShipmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOperatorOrAdmin]
    lookup_field = "uuid"
    filterset_class = ShipmentFilter
    search_fields = ["tracking_code", "reference", "recipient_name", "sender__company_name"]
    ordering_fields = ["created_at", "estimated_delivery_date", "status", "priority"]

    def get_queryset(self):
        return (
            Shipment.objects.select_related(
                "sender", "driver", "driver__user", "external_carrier", "created_by",
            )
            .prefetch_related("events")
            .all()
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ShipmentListSerializer
        if self.action == "create":
            return ShipmentCreateSerializer
        return ShipmentDetailSerializer

    @action(detail=True, methods=["post"])
    def transition(self, request, uuid=None):
        shipment = self.get_object()
        serializer = ShipmentTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            event = transition_shipment(
                shipment=shipment,
                new_status=serializer.validated_data["new_status"],
                user=request.user,
                description=serializer.validated_data.get("description", ""),
                location=serializer.validated_data.get("location", ""),
                latitude=serializer.validated_data.get("latitude"),
                longitude=serializer.validated_data.get("longitude"),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ShipmentEventSerializer(event).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def assign(self, request, uuid=None):
        shipment = self.get_object()
        serializer = ShipmentAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        driver_uuid = serializer.validated_data.get("driver_uuid")
        carrier_uuid = serializer.validated_data.get("external_carrier_uuid")

        if driver_uuid:
            driver = Driver.objects.get(uuid=driver_uuid)
            shipment.driver = driver
            shipment.delivery_type = "internal"
        elif carrier_uuid:
            carrier = ExternalCarrier.objects.get(uuid=carrier_uuid)
            shipment.external_carrier = carrier
            shipment.external_tracking_number = serializer.validated_data.get(
                "external_tracking_number", ""
            )
            shipment.delivery_type = "external"

        shipment.save()

        # Transizione a "assigned"
        if shipment.status == "created":
            try:
                transition_shipment(
                    shipment=shipment,
                    new_status="assigned",
                    user=request.user,
                    description="Spedizione assegnata",
                )
            except InvalidTransitionError:
                pass

        return Response(
            ShipmentDetailSerializer(shipment).data, status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def waybill(self, request, uuid=None):
        """Genera e restituisce il PDF del foglio di vettura."""
        from django.utils import timezone

        from .waybill import generate_waybill_pdf

        shipment = self.get_object()
        base_url = request.build_absolute_uri("/").rstrip("/")
        pdf_bytes = generate_waybill_pdf(shipment, base_url=base_url)

        # Segna la stampa
        shipment.waybill_printed_at = timezone.now()
        shipment.save(update_fields=["waybill_printed_at"])

        response = DjangoHttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="foglio_vettura_{shipment.tracking_code}.pdf"'
        )
        return response

    @action(detail=True, methods=["get"])
    def events(self, request, uuid=None):
        shipment = self.get_object()
        events = shipment.events.all()
        serializer = ShipmentEventSerializer(events, many=True)
        return Response(serializer.data)


class DriverShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Spedizioni assegnate al corriere loggato."""

    serializer_class = ShipmentListSerializer
    permission_classes = [IsDriver]

    def get_queryset(self):
        driver = self.request.user.driver_profile
        return (
            Shipment.objects.filter(driver=driver)
            .select_related("sender", "driver", "driver__user")
            .exclude(status__in=["cancelled", "returned"])
        )

    @action(detail=False, methods=["get"])
    def today(self, request):
        from django.utils import timezone

        today = timezone.localdate()
        qs = self.get_queryset().filter(
            estimated_delivery_date=today,
        ) | self.get_queryset().filter(
            status__in=["assigned", "picked_up", "in_transit", "out_for_delivery"],
        )
        serializer = self.get_serializer(qs.distinct(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="pickup")
    def pickup(self, request, pk=None):
        shipment = self.get_object()
        serializer = ShipmentTransitionSerializer(data={
            "new_status": "picked_up",
            **request.data,
        })
        serializer.is_valid(raise_exception=True)

        try:
            event = transition_shipment(
                shipment=shipment,
                new_status="picked_up",
                user=request.user,
                description="Merce ritirata dal corriere",
                latitude=serializer.validated_data.get("latitude"),
                longitude=serializer.validated_data.get("longitude"),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ShipmentEventSerializer(event).data)
