from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class User(AbstractUser, UUIDModel, TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Amministratore"
        OPERATOR = "operator", "Operatore"
        DRIVER = "driver", "Corriere"
        VIEWER = "viewer", "Solo lettura"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OPERATOR)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return self.get_full_name() or self.username
