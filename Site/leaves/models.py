from django.conf import settings
from django.db import models

from Freyja.mixins import TimeStampMixin
from departments.models import DepartmentEmployee


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

    employee = models.ForeignKey(
        DepartmentEmployee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.IntegerField(
        choices=LeaveType.choices,
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDING,
    )
    reason = models.TextField(blank=True, default="")
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

    @property
    def length(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def __str__(self) -> str:
        return f"{self.employee} leave from {self.start_date} to {self.end_date}"
