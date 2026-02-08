from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class NotificationLog(UUIDModel, TimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        WHATSAPP = "whatsapp", "WhatsApp"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        PENDING = "pending", "In coda"
        SENT = "sent", "Inviata"
        DELIVERED = "delivered", "Recapitata"
        FAILED = "failed", "Fallita"

    shipment = models.ForeignKey(
        "shipments.Shipment", on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    external_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "notifications_log"
        ordering = ["-created_at"]
        verbose_name = "Notifica"
        verbose_name_plural = "Notifiche"

    def __str__(self):
        return f"{self.channel} → {self.recipient} ({self.status})"
