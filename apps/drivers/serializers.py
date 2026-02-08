from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Driver, ExternalCarrier


class ExternalCarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalCarrier
        fields = ("uuid", "name", "code", "tracking_url_template", "is_active")
        read_only_fields = ("uuid",)


class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = (
            "uuid", "user", "vehicle_plate", "vehicle_type",
            "zone", "status", "max_daily_shipments", "is_active",
        )
        read_only_fields = ("uuid",)
