from rest_framework import serializers

from .models import Address, Customer


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "uuid", "label", "street", "city", "province",
            "postal_code", "country", "latitude", "longitude",
        )
        read_only_fields = ("uuid",)


class CustomerSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = (
            "uuid", "company_name", "contact_name", "email", "phone",
            "customer_type", "notes", "is_active", "addresses",
        )
        read_only_fields = ("uuid",)


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("uuid", "company_name", "contact_name", "email", "phone", "customer_type")
        read_only_fields = ("uuid",)
