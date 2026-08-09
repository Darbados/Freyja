import datetime
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from Freyja.mixins import TimeStampMixin
from employment.models import Employee


class Leave(TimeStampMixin):
    """Represents a leave request from an employee."""

    class LeaveType(models.IntegerChoices):
        ANNUAL = 1, "Annual"
        SICK = 2, "Sick"
        UNPAID = 3, "Unpaid"
        OTHER = 4, "Other"

    class Status(models.IntegerChoices):
        PENDING = 1, "Pending"
        APPROVED = 2, "Approved"
        REJECTED = 3, "Rejected"
        CANCELED = 4, "Canceled"

    class DayPart(models.TextChoices):
        FULL_DAY = "full_day", "Full day"
        FIRST_HALF = "first_half", "First half"
        SECOND_HALF = "second_half", "Second half"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    approver = models.ForeignKey(
        Employee,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="leave_requests_to_approve",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    start_day_part = models.CharField(
        max_length=20,
        choices=DayPart.choices,
        default=DayPart.FULL_DAY,
    )
    end_day_part = models.CharField(
        max_length=20,
        choices=DayPart.choices,
        default=DayPart.FULL_DAY,
    )
    leave_type = models.IntegerField(
        choices=LeaveType.choices,
        default=LeaveType.ANNUAL,
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDING,
    )
    comment = models.TextField(blank=True, default="")
    cancellation_reason = models.TextField(blank=True, default="")
    canceled_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_leaves",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="leave_end_date_on_or_after_start_date",
            ),
        ]
        ordering = ("-start_date", "-created_at")

    @property
    def duration_hours(self) -> Decimal:
        if not self.start_date or not self.end_date or self.end_date < self.start_date:
            return Decimal("0")

        workdays = sum(
            1
            for offset in range((self.end_date - self.start_date).days + 1)
            if (self.start_date + datetime.timedelta(days=offset)).weekday() < 5
        )
        if workdays == 0:
            return Decimal("0")
        if self.start_date == self.end_date:
            return Decimal("8") if self.start_day_part == self.DayPart.FULL_DAY else Decimal("4")

        hours = Decimal(workdays * 8)
        if self.start_day_part == self.DayPart.SECOND_HALF:
            hours -= Decimal("4")
        if self.end_day_part == self.DayPart.FIRST_HALF:
            hours -= Decimal("4")
        return hours

    @property
    def duration_days(self) -> Decimal:
        return self.duration_hours / Decimal("8")

    @property
    def can_cancel(self) -> bool:
        return (
            self.status in {self.Status.PENDING, self.Status.APPROVED}
            and self.end_date >= timezone.localdate()
        )

    def clean(self) -> None:
        super().clean()
        if not self.start_date or not self.end_date:
            return
        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "The end date cannot be before the start date."})
        if self.start_date.weekday() >= 5 or self.end_date.weekday() >= 5:
            raise ValidationError("Leave must start and end on a working day.")
        if self.start_date == self.end_date and self.start_day_part != self.end_day_part:
            raise ValidationError("Use the same day portion for a single-day request.")
        if self.start_date < self.end_date:
            if self.start_day_part == self.DayPart.FIRST_HALF:
                raise ValidationError(
                    {
                        "start_day_part": "A multi-day request can start with a full day or second half."
                    }
                )
            if self.end_day_part == self.DayPart.SECOND_HALF:
                raise ValidationError(
                    {"end_day_part": "A multi-day request can end with a full day or first half."}
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.employee} leave from {self.start_date} to {self.end_date}"
