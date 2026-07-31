from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from employment.models import EmploymentType, RelationshipKind


DEFAULT_EMPLOYMENT_TYPES = (
    {
        "code": "standard-employment",
        "name": "Standard employment",
        "relationship_kind": RelationshipKind.EMPLOYMENT,
        "paid_leave_eligible": True,
        "default_base_leave_days": Decimal("20.00"),
    },
    {
        "code": "civil-contract",
        "name": "Civil contract",
        "relationship_kind": RelationshipKind.CIVIL,
        "paid_leave_eligible": False,
        "default_base_leave_days": Decimal("0.00"),
    },
)


class Command(BaseCommand):
    help = "Creates the default employment types when they do not already exist."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0

        for definition in DEFAULT_EMPLOYMENT_TYPES:
            code = definition["code"]
            _, created = EmploymentType.objects.get_or_create(
                code=code,
                defaults={key: value for key, value in definition.items() if key != "code"},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created employment type: {code}"))
            else:
                self.stdout.write(f"Employment type already exists: {code}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Employment type seeding complete: {created_count} created, "
                f"{len(DEFAULT_EMPLOYMENT_TYPES) - created_count} unchanged."
            )
        )
