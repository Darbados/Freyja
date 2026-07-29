from django.conf import settings
from django.db import models


class Department(models.Model):
    """Represents a department."""

    name = models.CharField(max_length=255)
    director = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="departments",
    )

    def __str__(self) -> str:
        return self.name


class DepartmentEmployee(models.Model):
    """Represents a department employee assignment."""

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="employees",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="department_assignments",
    )

    def __str__(self) -> str:
        return f"{self.user} in {self.department}"
