import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    "created": "La tua spedizione {tracking_code} è stata creata.",
    "assigned": "La tua spedizione {tracking_code} è stata assegnata al corriere.",
    "picked_up": "La merce della spedizione {tracking_code} è stata ritirata.",
    "in_transit": "La spedizione {tracking_code} è in transito.",
    "out_for_delivery": "La spedizione {tracking_code} è in consegna. Il corriere sta arrivando.",
    "delivered": "La spedizione {tracking_code} è stata consegnata.",
    "not_delivered": "La spedizione {tracking_code} non è stata consegnata.",
    "returned": "La spedizione {tracking_code} è stata resa al mittente.",
}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_status_notification(self, shipment_id: int, new_status: str):
    from apps.notifications.models import NotificationLog
    from apps.shipments.models import Shipment

    try:
        shipment = Shipment.objects.select_related("sender").get(id=shipment_id)
    except Shipment.DoesNotExist:
        logger.error(f"Shipment {shipment_id} non trovata")
        return

    # Notifica al destinatario (se ha email)
    if shipment.recipient_email:
        _send_email_notification(shipment, new_status, shipment.recipient_email)

    # Notifica al mittente per stati significativi
    if new_status in ("delivered", "not_delivered", "returned") and shipment.sender.email:
        _send_email_notification(shipment, new_status, shipment.sender.email)


def _send_email_notification(shipment, new_status, recipient_email):
    from apps.notifications.models import NotificationLog

    tracking_code = shipment.tracking_code
    message_template = STATUS_MESSAGES.get(new_status, "")
    message = message_template.format(tracking_code=tracking_code)

    subject = f"Spedizione {tracking_code} - Aggiornamento stato"

    tracking_url = f"/t/{shipment.public_tracking_token}/"

    try:
        body = render_to_string("emails/status_notification.html", {
            "shipment": shipment,
            "message": message,
            "tracking_url": tracking_url,
            "new_status": new_status,
        })
    except Exception:
        body = f"{message}\n\nTracking: {tracking_url}"

    notification = NotificationLog.objects.create(
        shipment=shipment,
        channel="email",
        recipient=recipient_email,
        subject=subject,
        body=body,
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=body,
        )
        notification.status = "sent"
        notification.sent_at = timezone.now()
    except Exception as e:
        logger.error(f"Errore invio email a {recipient_email}: {e}")
        notification.status = "failed"
        notification.error_message = str(e)

    notification.save()
