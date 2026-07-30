from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from Freyja.mixins import TimeStampMixin


class FreyjaUser(TimeStampMixin, AbstractUser):
    """Represents a Freya's user."""

    email = models.EmailField(unique=True)
    manager = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def clean(self) -> None:
        super().clean()

        if self.manager is self:
            raise ValidationError({"manager": "A user cannot be their own manager."})

        if not self.manager_id:
            return

        seen_manager_ids = set()
        manager = self.manager

        while manager is not None:
            if manager.pk == self.pk:
                raise ValidationError({"manager": "A management cycle is not allowed."})

            if manager.pk in seen_manager_ids:
                raise ValidationError({"manager": "A management cycle is not allowed."})

            seen_manager_ids.add(manager.pk)
            manager = manager.manager

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.email
