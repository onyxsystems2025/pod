from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class Customer(UUIDModel, TimeStampedModel):
    class Type(models.TextChoices):
        SENDER = "sender", "Mittente"
        RECIPIENT = "recipient", "Destinatario"
        BOTH = "both", "Entrambi"

    company_name = models.CharField("Ragione sociale", max_length=255)
    contact_name = models.CharField("Referente", max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(
        max_length=10, choices=Type.choices, default=Type.BOTH
    )
    default_address = models.ForeignKey(
        "Address", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "customers_customer"
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name


class Address(UUIDModel, TimeStampedModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses",
    )
    label = models.CharField(max_length=100, blank=True, help_text="Es: Sede, Magazzino")
    street = models.CharField("Indirizzo", max_length=255)
    city = models.CharField("Città", max_length=100, db_index=True)
    province = models.CharField("Provincia", max_length=2)
    postal_code = models.CharField("CAP", max_length=10)
    country = models.CharField(max_length=2, default="IT")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "customers_address"
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.street}, {self.postal_code} {self.city} ({self.province})"
