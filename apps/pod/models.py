from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class PODRecord(UUIDModel, TimeStampedModel):
    class DeliveryResult(models.TextChoices):
        DELIVERED = "delivered", "Consegnata"
        PARTIAL = "partial", "Consegna parziale"
        REFUSED = "refused", "Rifiutata"
        DAMAGED = "damaged", "Danneggiata"
        ABSENT = "absent", "Destinatario assente"
        WRONG_ADDRESS = "wrong_address", "Indirizzo errato"
        OTHER = "other", "Altro"

    shipment = models.OneToOneField(
        "shipments.Shipment", on_delete=models.CASCADE, related_name="pod",
    )
    driver = models.ForeignKey(
        "drivers.Driver", on_delete=models.PROTECT, related_name="pod_records",
    )

    # Esito consegna
    delivery_result = models.CharField(
        "Esito", max_length=20, choices=DeliveryResult.choices,
    )
    recipient_signer_name = models.CharField(
        "Nome firmatario", max_length=255, blank=True,
    )
    notes = models.TextField("Note", blank=True)

    # Geolocalizzazione e timestamp
    recorded_at = models.DateTimeField(
        "Timestamp dispositivo",
        help_text="Timestamp catturato dal dispositivo del corriere",
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Firma digitale
    signature_image = models.ImageField(
        "Firma", upload_to="pod/signatures/%Y/%m/%d/", blank=True,
    )

    # Sincronizzazione offline
    synced_from_offline = models.BooleanField(default=False)
    device_uuid = models.CharField(max_length=64, blank=True)
    local_record_id = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "pod_record"
        verbose_name = "Proof of Delivery"
        verbose_name_plural = "Proof of Delivery"
        indexes = [
            models.Index(fields=["delivery_result", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device_uuid", "local_record_id"],
                name="unique_offline_pod",
                condition=models.Q(synced_from_offline=True),
            )
        ]

    def __str__(self):
        return f"POD {self.shipment.tracking_code} - {self.get_delivery_result_display()}"


class PODPhoto(UUIDModel, TimeStampedModel):
    pod_record = models.ForeignKey(
        PODRecord, on_delete=models.CASCADE, related_name="photos",
    )
    image = models.ImageField("Foto", upload_to="pod/photos/%Y/%m/%d/")
    caption = models.CharField(max_length=255, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "pod_photo"
        verbose_name = "Foto POD"
        verbose_name_plural = "Foto POD"

    def __str__(self):
        return f"Foto {self.pod_record.shipment.tracking_code}"
