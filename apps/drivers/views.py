from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsOperatorOrAdmin

from .models import Driver, ExternalCarrier
from .serializers import DriverSerializer, ExternalCarrierSerializer


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Driver.objects.filter(is_active=True).select_related("user")
    serializer_class = DriverSerializer
    permission_classes = [IsOperatorOrAdmin]
    lookup_field = "uuid"

    @action(detail=False, methods=["get"])
    def available(self, request):
        drivers = self.get_queryset().filter(status="available")
        serializer = self.get_serializer(drivers, many=True)
        return Response(serializer.data)


class ExternalCarrierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalCarrier.objects.filter(is_active=True)
    serializer_class = ExternalCarrierSerializer
    permission_classes = [IsOperatorOrAdmin]
    lookup_field = "uuid"
