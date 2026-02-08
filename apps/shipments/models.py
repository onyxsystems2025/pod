import secrets

from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, UUIDModel


def generate_tracking_code():
    return f"POD-{secrets.token_hex(4).upper()}"


class Shipment(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Creata"
        ASSIGNED = "assigned", "Assegnata"
        PICKED_UP = "picked_up", "Presa in carico"
        IN_TRANSIT = "in_transit", "In transito"
        OUT_FOR_DELIVERY = "out_for_delivery", "In consegna"
        DELIVERED = "delivered", "Consegnata"
        NOT_DELIVERED = "not_delivered", "Non consegnata"
        RETURNED = "returned", "Resa al mittente"
        CANCELLED = "cancelled", "Annullata"

    class Priority(models.TextChoices):
        LOW = "low", "Bassa"
        NORMAL = "normal", "Normale"
        HIGH = "high", "Alta"
        URGENT = "urgent", "Urgente"

    class DeliveryType(models.TextChoices):
        INTERNAL = "internal", "Corriere interno"
        EXTERNAL = "external", "Corriere esterno"

    # Identificativi
    tracking_code = models.CharField(
        max_length=20, unique=True, default=generate_tracking_code, db_index=True,
    )
    reference = models.CharField(
        "Riferimento ordine", max_length=100, blank=True, db_index=True,
    )

    # Mittente
    sender = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT,
        related_name="shipments_as_sender", verbose_name="Mittente",
    )
    sender_address = models.ForeignKey(
        "customers.Address", on_delete=models.PROTECT,
        related_name="shipments_from", null=True, blank=True,
    )

    # Destinatario
    recipient_name = models.CharField("Nome destinatario", max_length=255)
    recipient_phone = models.CharField("Telefono destinatario", max_length=20, blank=True)
    recipient_email = models.EmailField("Email destinatario", blank=True)
    delivery_address = models.ForeignKey(
        "customers.Address", on_delete=models.PROTECT,
        related_name="shipments_to", null=True, blank=True,
    )
    # Indirizzo inline per destinatari non ricorrenti
    delivery_street = models.CharField(max_length=255, blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_province = models.CharField(max_length=2, blank=True)
    delivery_postal_code = models.CharField(max_length=10, blank=True)

    # Stato e assegnazione
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED, db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL,
    )
    delivery_type = models.CharField(
        max_length=10, choices=DeliveryType.choices, default=DeliveryType.INTERNAL,
    )

    # Corriere interno
    driver = models.ForeignKey(
        "drivers.Driver", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="shipments",
    )
    # Corriere esterno
    external_carrier = models.ForeignKey(
        "drivers.ExternalCarrier", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="shipments",
    )
    external_tracking_number = models.CharField(max_length=100, blank=True, db_index=True)

    # Dettagli
    description = models.TextField("Descrizione merce", blank=True)
    packages_count = models.PositiveIntegerField("Numero colli", default=1)
    weight_kg = models.DecimalField(
        "Peso (kg)", max_digits=8, decimal_places=2, null=True, blank=True,
    )
    notes_internal = models.TextField("Note interne", blank=True)

    # Date
    estimated_delivery_date = models.DateField("Data consegna prevista", null=True, blank=True)
    actual_delivery_date = models.DateTimeField("Data consegna effettiva", null=True, blank=True)
    picked_up_at = models.DateTimeField("Data ritiro", null=True, blank=True)

    # Foglio di vettura
    waybill_printed_at = models.DateTimeField("Data stampa foglio vettura", null=True, blank=True)

    # Tracking pubblico
    public_tracking_token = models.CharField(
        max_length=64, unique=True, editable=False, db_index=True,
    )

    # Operatore
    created_by = models.ForeignKey(
        "accounts.User", null=True, on_delete=models.SET_NULL,
        related_name="created_shipments",
    )

    class Meta:
        db_table = "shipments_shipment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["delivery_type", "status"]),
            models.Index(fields=["sender", "status"]),
            models.Index(fields=["driver", "status"]),
            models.Index(fields=["estimated_delivery_date"]),
        ]

    def save(self, *args, **kwargs):
        if not self.public_tracking_token:
            self.public_tracking_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_code} - {self.recipient_name}"

    def get_effective_delivery_address(self) -> str:
        if self.delivery_address:
            return str(self.delivery_address)
        parts = filter(None, [
            self.delivery_street,
            f"{self.delivery_postal_code} {self.delivery_city}".strip(),
            f"({self.delivery_province})" if self.delivery_province else "",
        ])
        return ", ".join(parts)

    def get_external_tracking_url(self) -> str:
        if self.external_carrier and self.external_tracking_number:
            return self.external_carrier.get_tracking_url(self.external_tracking_number)
        return ""


class ShipmentEvent(UUIDModel, TimeStampedModel):
    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="events",
    )
    status = models.CharField(max_length=20, choices=Shipment.Status.choices)
    description = models.CharField(max_length=500)
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    recorded_by = models.ForeignKey(
        "accounts.User", null=True, on_delete=models.SET_NULL,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "shipments_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shipment", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.shipment.tracking_code} - {self.get_status_display()}"
