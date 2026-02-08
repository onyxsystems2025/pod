"""Generazione foglio di vettura PDF con QR code."""
import io

import qrcode
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML


def generate_qr_code_data_uri(url: str) -> str:
    """Genera un QR code e lo restituisce come data URI base64."""
    import base64

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def generate_waybill_pdf(shipment, base_url: str = "") -> bytes:
    """Genera il PDF del foglio di vettura per una spedizione."""
    if not base_url:
        base_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    qr_url = f"{base_url}/qr/{shipment.uuid}/"
    qr_data_uri = generate_qr_code_data_uri(qr_url)

    context = {
        "shipment": shipment,
        "qr_data_uri": qr_data_uri,
        "qr_url": qr_url,
        "tracking_url": f"{base_url}/t/{shipment.public_tracking_token}/",
        "generated_at": timezone.now(),
        "sender_address": shipment.sender_address,
        "delivery_address_display": shipment.get_effective_delivery_address(),
    }

    html_string = render_to_string("pod/waybill.html", context)
    pdf_buffer = io.BytesIO()
    HTML(string=html_string).write_pdf(pdf_buffer)
    return pdf_buffer.getvalue()
