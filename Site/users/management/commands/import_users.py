import csv
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from employment.models import Employee


REQUIRED_COLUMNS = {"email", "name", "job", "manager_email", "role", "is_active"}
VALID_ROLES = {"ADMIN", "MANAGER", "USER"}


class Command(BaseCommand):
    help = "Imports Freyja users and their employee management hierarchy from CSV."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("csv_path", type=Path)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and process the CSV without committing database changes.",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        csv_path: Path = options["csv_path"]
        dry_run: bool = options["dry_run"]

        if not csv_path.is_file():
            raise CommandError(f"CSV file does not exist: {csv_path}")

        rows = self._read_and_validate_rows(csv_path)
        self._validate_management_hierarchy(rows)

        user_model = get_user_model()
        employees_by_email = {}
        users_created = 0
        users_updated = 0
        employees_created = 0

        for row in rows:
            email = row["email"]
            name_parts = row["name"].split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1].strip() if len(name_parts) == 2 else ""
            is_superuser = row["role"] == "ADMIN"

            user = user_model.objects.filter(email__iexact=email).first()
            if user is None:
                user = user_model.objects.create_user(
                    username=email,
                    email=email,
                    password=None,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=row["is_active"] == "1",
                    is_staff=is_superuser,
                    is_superuser=is_superuser,
                )
                users_created += 1
            else:
                user.email = email
                user.username = email
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = row["is_active"] == "1"
                user.is_staff = is_superuser
                user.is_superuser = is_superuser
                user.save(
                    update_fields=(
                        "email",
                        "username",
                        "first_name",
                        "last_name",
                        "is_active",
                        "is_staff",
                        "is_superuser",
                        "updated_at",
                    )
                )
                users_updated += 1

            employee, employee_created = Employee.objects.get_or_create(
                user=user,
                defaults={"job_title": row["job_title"]},
            )
            if not employee_created and employee.job_title != row["job_title"]:
                employee.job_title = row["job_title"]
                employee.save(update_fields=("job_title", "updated_at"))
            employees_created += int(employee_created)
            employees_by_email[email] = employee

        employees_to_update = []
        updated_at = timezone.now()
        for row in rows:
            employee = employees_by_email[row["email"]]
            manager_email = row["manager_email"]
            employee.manager = employees_by_email.get(manager_email) if manager_email else None
            employee.updated_at = updated_at
            employees_to_update.append(employee)

        Employee.objects.bulk_update(employees_to_update, ("manager", "updated_at"))

        if dry_run:
            transaction.set_rollback(True)

        action = "Dry run complete" if dry_run else "Import complete"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: {users_created} users created, {users_updated} users updated, "
                f"{employees_created} employees created, "
                f"{sum(bool(row['manager_email']) for row in rows)} managers assigned."
            )
        )

    def _read_and_validate_rows(self, csv_path: Path) -> list[dict[str, str]]:
        rows = []
        seen_emails = set()

        with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames or ())
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise CommandError(f"CSV is missing required columns: {missing}")

            for row_number, source_row in enumerate(reader, start=2):
                row = {
                    "email": source_row["email"].strip().lower(),
                    "name": source_row["name"].strip(),
                    "job_title": source_row["job"].strip(),
                    "manager_email": source_row["manager_email"].strip().lower(),
                    "role": source_row["role"].strip().upper(),
                    "is_active": source_row["is_active"].strip(),
                }

                if not row["email"] or not row["name"]:
                    raise CommandError(f"Row {row_number}: email and name are required.")
                if row["email"] in seen_emails:
                    raise CommandError(f"Row {row_number}: duplicate email {row['email']!r}.")
                if row["role"] not in VALID_ROLES:
                    raise CommandError(f"Row {row_number}: unsupported role {row['role']!r}.")
                if row["is_active"] not in {"0", "1"}:
                    raise CommandError(f"Row {row_number}: is_active must be either '0' or '1'.")

                seen_emails.add(row["email"])
                rows.append(row)

        return rows

    def _validate_management_hierarchy(self, rows: list[dict[str, str]]) -> None:
        managers_by_email = {row["email"]: row["manager_email"] for row in rows}

        for email, manager_email in managers_by_email.items():
            if manager_email and manager_email not in managers_by_email:
                raise CommandError(f"User {email!r} references unknown manager {manager_email!r}.")

            seen_emails = {email}
            current_email = manager_email
            while current_email:
                if current_email in seen_emails:
                    raise CommandError(f"Management cycle detected for user {email!r}.")
                seen_emails.add(current_email)
                current_email = managers_by_email[current_email]
