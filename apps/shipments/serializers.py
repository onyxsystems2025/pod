from rest_framework import serializers

from apps.customers.serializers import CustomerListSerializer
from apps.drivers.serializers import DriverSerializer, ExternalCarrierSerializer

from .models import Shipment, ShipmentEvent
from .state_machine import VALID_TRANSITIONS


class ShipmentEventSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True, default="")

    class Meta:
        model = ShipmentEvent
        fields = (
            "uuid", "status", "description", "location",
            "latitude", "longitude", "recorded_by_name", "created_at",
        )


class ShipmentListSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.company_name", read_only=True)
    driver_name = serializers.SerializerMethodField()
    delivery_address_display = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = (
            "uuid", "tracking_code", "reference", "recipient_name",
            "sender_name", "status", "priority", "delivery_type",
            "driver_name", "packages_count", "estimated_delivery_date",
            "delivery_address_display", "created_at",
        )

    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.user.get_full_name()
        if obj.external_carrier:
            return obj.external_carrier.name
        return ""

    def get_delivery_address_display(self, obj):
        return obj.get_effective_delivery_address()


class ShipmentDetailSerializer(serializers.ModelSerializer):
    sender = CustomerListSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)
    external_carrier = ExternalCarrierSerializer(read_only=True)
    events = ShipmentEventSerializer(many=True, read_only=True)
    delivery_address_display = serializers.SerializerMethodField()
    external_tracking_url = serializers.SerializerMethodField()
    allowed_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = (
            "uuid", "tracking_code", "reference",
            "sender", "sender_address",
            "recipient_name", "recipient_phone", "recipient_email",
            "delivery_address", "delivery_street", "delivery_city",
            "delivery_province", "delivery_postal_code",
            "delivery_address_display",
            "status", "priority", "delivery_type",
            "driver", "external_carrier", "external_tracking_number",
            "external_tracking_url",
            "description", "packages_count", "weight_kg", "notes_internal",
            "estimated_delivery_date", "actual_delivery_date", "picked_up_at",
            "waybill_printed_at",
            "events", "allowed_transitions",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "uuid", "tracking_code", "public_tracking_token",
            "actual_delivery_date", "picked_up_at", "waybill_printed_at",
        )

    def get_delivery_address_display(self, obj):
        return obj.get_effective_delivery_address()

    def get_external_tracking_url(self, obj):
        return obj.get_external_tracking_url()

    def get_allowed_transitions(self, obj):
        return VALID_TRANSITIONS.get(obj.status, [])


class ShipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = (
            "sender", "sender_address",
            "recipient_name", "recipient_phone", "recipient_email",
            "delivery_address", "delivery_street", "delivery_city",
            "delivery_province", "delivery_postal_code",
            "delivery_type", "priority", "reference",
            "description", "packages_count", "weight_kg",
            "notes_internal", "estimated_delivery_date",
            "driver", "external_carrier", "external_tracking_number",
        )

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        shipment = super().create(validated_data)
        # Crea evento iniziale
        ShipmentEvent.objects.create(
            shipment=shipment,
            status="created",
            description="Spedizione creata",
            recorded_by=self.context["request"].user,
        )
        return shipment


class ShipmentTransitionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=Shipment.Status.choices)
    description = serializers.CharField(required=False, default="")
    location = serializers.CharField(required=False, default="")
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True,
    )


class ShipmentAssignSerializer(serializers.Serializer):
    driver_uuid = serializers.UUIDField(required=False, allow_null=True)
    external_carrier_uuid = serializers.UUIDField(required=False, allow_null=True)
    external_tracking_number = serializers.CharField(required=False, default="")
