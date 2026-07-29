from django.contrib.auth.models import AbstractUser
from django.db import models

from Freyja.mixins import TimeStampMixin


class FreyjaUser(TimeStampMixin, AbstractUser):
    """Represents a Freya's user."""

    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self) -> str:
        return self.email
