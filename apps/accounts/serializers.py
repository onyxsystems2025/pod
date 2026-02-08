from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("uuid", "username", "email", "first_name", "last_name", "role", "phone")
        read_only_fields = ("uuid",)


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid", "username", "email", "first_name", "last_name",
            "role", "phone", "date_joined",
        )
        read_only_fields = ("uuid", "username", "role", "date_joined")
