from rest_framework import viewsets

from apps.accounts.permissions import IsOperatorOrAdmin

from .models import Address, Customer
from .serializers import AddressSerializer, CustomerListSerializer, CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.filter(is_active=True).prefetch_related("addresses")
    permission_classes = [IsOperatorOrAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return CustomerListSerializer
        return CustomerSerializer


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsOperatorOrAdmin]

    def get_queryset(self):
        return Address.objects.filter(customer__uuid=self.kwargs["customer_uuid"])

    def perform_create(self, serializer):
        customer = Customer.objects.get(uuid=self.kwargs["customer_uuid"])
        serializer.save(customer=customer)
