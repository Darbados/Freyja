from django.conf import settings
from django.db import models


class UserAdministrationEvent(models.Model):
    """Records immutable security-sensitive backoffice user operations."""

    class Action(models.TextChoices):
        DEACTIVATED = "deactivated", "Deactivated"
        CONFIRMATION_SENT = "confirmation_sent", "Confirmation sent"

    action = models.CharField(max_length=32, choices=Action)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="administration_events",
    )
    target_email = models.EmailField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="performed_administration_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
