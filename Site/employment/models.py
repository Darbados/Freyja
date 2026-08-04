from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from Freyja.mixins import TimeStampMixin


class RelationshipKind(models.TextChoices):
    EMPLOYMENT = "employment", "Employment contract"
    CIVIL = "civil", "Civil contract"


class EmploymentType(TimeStampMixin):
    """Represents configurable defaults for an employment relationship."""

    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)
    relationship_kind = models.CharField(
        max_length=20,
        choices=RelationshipKind.choices,
    )
    paid_leave_eligible = models.BooleanField(default=True)
    default_base_leave_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Employee(TimeStampMixin):
    """Adds employment-specific information to a Freyja user account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    job_title = models.CharField(max_length=255, blank=True, default="")
    manager = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )
    leave_approver = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="leave_approval_assignments",
    )

    def clean(self) -> None:
        super().clean()

        if self.pk and self.leave_approver_id == self.pk:
            raise ValidationError(
                {"leave_approver": "An employee cannot approve their own leave."}
            )

        if not self.manager_id:
            return

        if self.pk and self.manager_id == self.pk:
            raise ValidationError({"manager": "An employee cannot be their own manager."})

        seen_manager_ids = set()
        manager = self.manager

        while manager is not None:
            if manager.pk == self.pk or manager.pk in seen_manager_ids:
                raise ValidationError({"manager": "A management cycle is not allowed."})

            seen_manager_ids.add(manager.pk)
            manager = manager.manager

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.user)


class Employment(TimeStampMixin):
    """Represents one employee relationship over a defined period."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employments",
    )
    employment_type = models.ForeignKey(
        EmploymentType,
        on_delete=models.PROTECT,
        related_name="employments",
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    base_leave_days_override = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ("-start_date", "-id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="employment_end_on_or_after_start",
            ),
        ]

    @property
    def base_leave_days(self) -> Decimal:
        if self.base_leave_days_override is not None:
            return self.base_leave_days_override

        return self.employment_type.default_base_leave_days

    def __str__(self) -> str:
        return f"{self.employee} — {self.employment_type}"
