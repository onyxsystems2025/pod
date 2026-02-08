from rest_framework import generics, permissions

from .models import User
from .serializers import UserMeSerializer


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
