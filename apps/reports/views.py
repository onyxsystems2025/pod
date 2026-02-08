import csv

from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsOperatorOrAdmin
from apps.shipments.models import Shipment


class DashboardStatsView(APIView):
    permission_classes = [IsOperatorOrAdmin]

    def get(self, request):
        from django.db.models import Count, Q
        from django.utils import timezone

        today = timezone.localdate()

        stats = Shipment.objects.aggregate(
            total=Count("id"),
            created=Count("id", filter=Q(status="created")),
            assigned=Count("id", filter=Q(status="assigned")),
            in_transit=Count("id", filter=Q(status__in=["picked_up", "in_transit"])),
            out_for_delivery=Count("id", filter=Q(status="out_for_delivery")),
            delivered_today=Count(
                "id",
                filter=Q(status="delivered", actual_delivery_date__date=today),
            ),
            not_delivered=Count("id", filter=Q(status="not_delivered")),
        )

        return Response(stats)


class DeliveriesExportCSVView(APIView):
    permission_classes = [IsOperatorOrAdmin]

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        qs = Shipment.objects.select_related(
            "sender", "driver", "driver__user", "external_carrier",
        ).order_by("-created_at")

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="spedizioni.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Tracking", "Riferimento", "Mittente", "Destinatario",
            "Indirizzo consegna", "Stato", "Tipo consegna",
            "Corriere", "Colli", "Peso (kg)",
            "Data creazione", "Data consegna prevista", "Data consegna effettiva",
        ])

        for s in qs:
            driver_name = ""
            if s.driver:
                driver_name = s.driver.user.get_full_name()
            elif s.external_carrier:
                driver_name = s.external_carrier.name

            writer.writerow([
                s.tracking_code,
                s.reference,
                s.sender.company_name,
                s.recipient_name,
                s.get_effective_delivery_address(),
                s.get_status_display(),
                s.get_delivery_type_display(),
                driver_name,
                s.packages_count,
                s.weight_kg or "",
                s.created_at.strftime("%d/%m/%Y %H:%M"),
                s.estimated_delivery_date.strftime("%d/%m/%Y") if s.estimated_delivery_date else "",
                s.actual_delivery_date.strftime("%d/%m/%Y %H:%M") if s.actual_delivery_date else "",
            ])

        return response
