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
    email_confirmed_at = models.DateTimeField(blank=True, null=True)
    totp_secret = models.TextField(blank=True, default="")
    two_factor_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email
