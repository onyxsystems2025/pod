from typing import Optional

from django.utils import timezone

VALID_TRANSITIONS = {
    "created": ["assigned", "cancelled"],
    "assigned": ["picked_up", "cancelled", "created"],
    "picked_up": ["in_transit", "cancelled"],
    "in_transit": ["out_for_delivery", "cancelled"],
    "out_for_delivery": ["delivered", "not_delivered"],
    "delivered": [],
    "not_delivered": ["out_for_delivery", "returned", "cancelled"],
    "returned": [],
    "cancelled": [],
}


class InvalidTransitionError(Exception):
    pass


def validate_transition(current_status: str, new_status: str) -> bool:
    allowed = VALID_TRANSITIONS.get(current_status, [])
    return new_status in allowed


def transition_shipment(
    shipment,
    new_status: str,
    user=None,
    description: str = "",
    location: str = "",
    latitude=None,
    longitude=None,
    metadata: Optional[dict] = None,
):
    from apps.shipments.models import ShipmentEvent

    if not validate_transition(shipment.status, new_status):
        raise InvalidTransitionError(
            f"Transizione non valida: {shipment.status} -> {new_status}"
        )

    old_status = shipment.status
    shipment.status = new_status

    update_fields = ["status", "updated_at"]

    if new_status == "delivered":
        shipment.actual_delivery_date = timezone.now()
        update_fields.append("actual_delivery_date")
    elif new_status == "picked_up":
        shipment.picked_up_at = timezone.now()
        update_fields.append("picked_up_at")

    shipment.save(update_fields=update_fields)

    event = ShipmentEvent.objects.create(
        shipment=shipment,
        status=new_status,
        description=description or f"Stato cambiato: {old_status} → {new_status}",
        location=location,
        latitude=latitude,
        longitude=longitude,
        recorded_by=user,
        metadata=metadata or {},
    )

    # Trigger notifica asincrona
    from apps.notifications.tasks import send_status_notification

    send_status_notification.delay(shipment.id, new_status)

    return event
