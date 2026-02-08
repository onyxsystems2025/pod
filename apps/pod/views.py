from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsDriver
from apps.shipments.models import Shipment
from apps.shipments.state_machine import InvalidTransitionError, transition_shipment

from .models import PODPhoto, PODRecord
from .serializers import (
    PODCreateSerializer,
    PODPhotoSerializer,
    PODRecordSerializer,
    PODSyncSerializer,
)


class PODCreateView(APIView):
    """Crea un record POD per una spedizione (dal corriere)."""

    permission_classes = [IsDriver]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, shipment_uuid):
        shipment = get_object_or_404(Shipment, uuid=shipment_uuid)
        serializer = PODCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        driver = request.user.driver_profile

        # Determina lo stato di transizione in base al risultato
        delivery_result = data["delivery_result"]
        if delivery_result == "delivered":
            new_status = "delivered"
        elif delivery_result == "partial":
            new_status = "delivered"
        else:
            new_status = "not_delivered"

        try:
            pod_record = PODRecord.objects.create(
                shipment=shipment,
                driver=driver,
                delivery_result=delivery_result,
                recipient_signer_name=data.get("recipient_signer_name", ""),
                notes=data.get("notes", ""),
                recorded_at=data["recorded_at"],
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                signature_image=data.get("signature_image"),
                synced_from_offline=data.get("synced_from_offline", False),
                device_uuid=data.get("device_uuid", ""),
                local_record_id=data.get("local_record_id", ""),
            )
        except IntegrityError:
            # Record offline già sincronizzato (dedup)
            pod_record = PODRecord.objects.get(
                device_uuid=data["device_uuid"],
                local_record_id=data["local_record_id"],
            )
            return Response(
                PODRecordSerializer(pod_record).data,
                status=status.HTTP_200_OK,
            )

        # Transizione di stato della spedizione
        try:
            transition_shipment(
                shipment=shipment,
                new_status=new_status,
                user=request.user,
                description=f"POD registrato: {pod_record.get_delivery_result_display()}",
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
            )
        except InvalidTransitionError:
            pass  # La spedizione potrebbe già essere nello stato finale

        return Response(
            PODRecordSerializer(pod_record).data,
            status=status.HTTP_201_CREATED,
        )


class PODDetailView(generics.RetrieveAPIView):
    queryset = PODRecord.objects.prefetch_related("photos")
    serializer_class = PODRecordSerializer
    lookup_field = "uuid"


class PODPhotoUploadView(APIView):
    """Upload foto aggiuntive per un POD."""

    permission_classes = [IsDriver]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pod_uuid):
        pod_record = get_object_or_404(PODRecord, uuid=pod_uuid)
        image = request.FILES.get("image")
        if not image:
            return Response(
                {"error": "Nessuna immagine fornita"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photo = PODPhoto.objects.create(
            pod_record=pod_record,
            image=image,
            caption=request.data.get("caption", ""),
            taken_at=request.data.get("taken_at"),
        )
        return Response(PODPhotoSerializer(photo).data, status=status.HTTP_201_CREATED)


class PODSyncView(APIView):
    """Sincronizzazione batch di record POD offline."""

    permission_classes = [IsDriver]

    def post(self, request):
        serializer = PODSyncSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        results = []
        driver = request.user.driver_profile

        for record_data in serializer.validated_data:
            shipment = get_object_or_404(
                Shipment, uuid=record_data["shipment_uuid"],
            )

            delivery_result = record_data["delivery_result"]
            if delivery_result in ("delivered", "partial"):
                new_status = "delivered"
            else:
                new_status = "not_delivered"

            try:
                pod_record = PODRecord.objects.create(
                    shipment=shipment,
                    driver=driver,
                    delivery_result=delivery_result,
                    recipient_signer_name=record_data.get("recipient_signer_name", ""),
                    notes=record_data.get("notes", ""),
                    recorded_at=record_data["recorded_at"],
                    latitude=record_data.get("latitude"),
                    longitude=record_data.get("longitude"),
                    synced_from_offline=True,
                    device_uuid=record_data["device_uuid"],
                    local_record_id=record_data["local_record_id"],
                )

                try:
                    transition_shipment(
                        shipment=shipment,
                        new_status=new_status,
                        user=request.user,
                        description=f"POD offline sincronizzato: {pod_record.get_delivery_result_display()}",
                        latitude=record_data.get("latitude"),
                        longitude=record_data.get("longitude"),
                    )
                except InvalidTransitionError:
                    pass

                results.append({
                    "local_record_id": record_data["local_record_id"],
                    "status": "created",
                    "uuid": str(pod_record.uuid),
                })
            except IntegrityError:
                results.append({
                    "local_record_id": record_data["local_record_id"],
                    "status": "duplicate",
                })

        return Response({"results": results})


class QRCodeRedirectView(View):
    """Redirect dal QR code al form POD nella PWA."""

    def get(self, request, shipment_uuid):
        shipment = get_object_or_404(Shipment, uuid=shipment_uuid)
        # Redirect alla PWA con il UUID della spedizione
        return redirect(f"/pwa/pod/{shipment.uuid}/")


class PWAView(View):
    """Serve la PWA corriere."""

    def get(self, request, *args, **kwargs):
        from django.shortcuts import render

        return render(request, "pod/pwa.html")


class PWAOfflineView(View):
    """Pagina offline della PWA."""

    def get(self, request):
        from django.shortcuts import render

        return render(request, "pod/offline.html")
