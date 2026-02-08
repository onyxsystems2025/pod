from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class ExternalCarrier(UUIDModel, TimeStampedModel):
    """Corriere terzo (BRT, GLS, SDA, ecc.)."""

    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=20, unique=True)
    tracking_url_template = models.URLField(
        blank=True,
        help_text="URL template. Usa {tracking_number} come placeholder.",
    )
    api_endpoint = models.URLField(blank=True)
    api_credentials = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "drivers_external_carrier"
        verbose_name = "Corriere esterno"
        verbose_name_plural = "Corrieri esterni"

    def __str__(self):
        return self.name

    def get_tracking_url(self, tracking_number: str) -> str:
        if self.tracking_url_template:
            return self.tracking_url_template.replace("{tracking_number}", tracking_number)
        return ""


class Driver(UUIDModel, TimeStampedModel):
    """Corriere interno (dipendente)."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponibile"
        ON_DELIVERY = "on_delivery", "In consegna"
        OFF_DUTY = "off_duty", "Fuori servizio"

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="driver_profile",
    )
    vehicle_plate = models.CharField("Targa", max_length=20, blank=True)
    vehicle_type = models.CharField("Tipo veicolo", max_length=50, blank=True)
    zone = models.CharField(
        "Zona operativa", max_length=100, blank=True,
        help_text="Zona operativa abituale",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE,
    )
    max_daily_shipments = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "drivers_driver"
        verbose_name = "Corriere"
        verbose_name_plural = "Corrieri"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.vehicle_plate})"
