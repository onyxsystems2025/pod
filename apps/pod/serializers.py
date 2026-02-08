from rest_framework import serializers

from .models import PODPhoto, PODRecord


class PODPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PODPhoto
        fields = ("uuid", "image", "caption", "taken_at")
        read_only_fields = ("uuid",)


class PODRecordSerializer(serializers.ModelSerializer):
    photos = PODPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = PODRecord
        fields = (
            "uuid", "delivery_result", "recipient_signer_name", "notes",
            "recorded_at", "latitude", "longitude",
            "signature_image", "photos",
            "synced_from_offline", "created_at",
        )
        read_only_fields = ("uuid",)


class PODCreateSerializer(serializers.Serializer):
    delivery_result = serializers.ChoiceField(choices=PODRecord.DeliveryResult.choices)
    recipient_signer_name = serializers.CharField(required=False, default="")
    notes = serializers.CharField(required=False, default="")
    recorded_at = serializers.DateTimeField()
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True,
    )
    signature_image = serializers.ImageField(required=False)

    # Offline sync fields
    synced_from_offline = serializers.BooleanField(default=False)
    device_uuid = serializers.CharField(required=False, default="")
    local_record_id = serializers.CharField(required=False, default="")


class PODSyncSerializer(serializers.Serializer):
    """Serializer per sync batch di record offline."""

    shipment_uuid = serializers.UUIDField()
    delivery_result = serializers.ChoiceField(choices=PODRecord.DeliveryResult.choices)
    recipient_signer_name = serializers.CharField(required=False, default="")
    notes = serializers.CharField(required=False, default="")
    recorded_at = serializers.DateTimeField()
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True,
    )
    device_uuid = serializers.CharField()
    local_record_id = serializers.CharField()
