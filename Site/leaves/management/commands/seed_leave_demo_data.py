import random
from collections import defaultdict
import datetime
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from departments.models import Department, DepartmentEmployee
from employment.models import Employee, Employment, EmploymentType, RelationshipKind
from leaves.models import Leave


SAMPLE_COMMENT = "Sample leave request generated for development."
DEPARTMENT_NAMES = {
    "ivailo@ebag.bg": "Technology",
    "hristiyan@ebag.bg": "Strategic Projects & Procurement",
    "mladen.borisov@ebag.bg": "Marketing",
    "miglena@ebag.bg": "Administration, Finance & HR",
    "milen@ebag.bg": "Commercial",
    "ventseslav@ebag.bg": "Logistics",
    "rosen.georgiev@ebag.bg": "Product",
    "silvia.andreeva@ebag.bg": "Customer Service",
    "adelina.georgieva@ebag.bg": "Legal",
    "maya.chausheva@ebag.bg": "IT Consulting",
}


class Command(BaseCommand):
    help = "Creates deterministic employment, department, and leave demo data."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        generator = random.Random(options["seed"])
        employees = list(Employee.objects.select_related("user", "manager__user"))
        if not employees:
            raise CommandError("No employees exist. Import users before seeding leave data.")

        ceo = next((employee for employee in employees if employee.job_title.lower() == "ceo"), None)
        cto = next(
            (
                employee
                for employee in employees
                if "технически директор" in employee.job_title.lower()
            ),
            None,
        )
        if ceo is None or cto is None:
            raise CommandError("The existing employee data must contain a CEO and CTO.")

        employment_type, _ = EmploymentType.objects.update_or_create(
            code="standard-full-time",
            defaults={
                "name": "Standard full-time employment",
                "relationship_kind": RelationshipKind.EMPLOYMENT,
                "paid_leave_eligible": True,
                "default_base_leave_days": Decimal("20"),
                "is_active": True,
            },
        )
        employment_starts = self._employment_starts(employees, ceo, cto, generator)
        employments_created = 0
        for employee in employees:
            _, created = Employment.objects.get_or_create(
                employee=employee,
                defaults={
                    "employment_type": employment_type,
                    "start_date": employment_starts[employee.id],
                    "base_leave_days_override": Decimal("20"),
                },
            )
            employments_created += int(created)

        memberships_created = self._create_departments(employees, ceo)
        leaves_created = self._create_leaves(employees, generator)

        if options["dry_run"]:
            transaction.set_rollback(True)

        action = "Dry run complete" if options["dry_run"] else "Demo data created"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: {employments_created} employments, "
                f"{memberships_created} department memberships, "
                f"{leaves_created} leave requests."
            )
        )

    def _employment_starts(
        self,
        employees: list[Employee],
        ceo: Employee,
        cto: Employee,
        generator: random.Random,
    ) -> dict[int, datetime.date]:
        today = timezone.localdate()
        earliest = datetime.date(today.year - 8, 1, 1)
        random_start = earliest + datetime.timedelta(days=62)
        available_days = (today - random_start).days
        starts = {
            ceo.id: earliest,
            cto.id: earliest + datetime.timedelta(days=31),
        }
        for employee in employees:
            if employee.id not in starts:
                starts[employee.id] = random_start + datetime.timedelta(
                    days=generator.randint(0, available_days)
                )
        return starts

    def _create_departments(self, employees: list[Employee], ceo: Employee) -> int:
        children: dict[int, list[Employee]] = defaultdict(list)
        for employee in employees:
            if employee.manager_id:
                children[employee.manager_id].append(employee)

        executive, _ = Department.objects.get_or_create(
            name="Executive",
            defaults={"director": ceo.user},
        )
        if executive.director_id != ceo.user_id:
            executive.director = ceo.user
            executive.save(update_fields=("director",))
        _, created = DepartmentEmployee.objects.get_or_create(
            department=executive,
            user=ceo.user,
        )
        memberships_created = int(created)

        for director in children.get(ceo.id, []):
            name = DEPARTMENT_NAMES.get(
                director.user.email,
                f"{director.user.get_full_name() or director.user.email} team",
            )
            department, _ = Department.objects.get_or_create(
                name=name,
                defaults={"director": director.user},
            )
            if department.director_id != director.user_id:
                department.director = director.user
                department.save(update_fields=("director",))

            stack = [director]
            while stack:
                member = stack.pop()
                _, created = DepartmentEmployee.objects.get_or_create(
                    department=department,
                    user=member.user,
                )
                memberships_created += int(created)
                stack.extend(children.get(member.id, []))

        return memberships_created

    def _create_leaves(
        self,
        employees: list[Employee],
        generator: random.Random,
    ) -> int:
        year = timezone.localdate().year
        range_start = datetime.date(year, 1, 1)
        range_end = datetime.date(year, 12, 15)
        available_days = (range_end - range_start).days
        created_count = 0

        for employee in employees:
            if employee.leave_requests.filter(comment=SAMPLE_COMMENT).exists():
                continue

            start = range_start + datetime.timedelta(days=generator.randint(0, available_days))
            while start.weekday() >= 5:
                start += datetime.timedelta(days=1)
            duration = generator.randint(1, 5)
            end = self._add_workdays(start, duration - 1)
            status = generator.choices(
                population=(
                    Leave.Status.APPROVED,
                    Leave.Status.PENDING,
                    Leave.Status.REJECTED,
                    Leave.Status.CANCELED,
                ),
                weights=(70, 20, 5, 5),
                k=1,
            )[0]
            leave_type = generator.choices(
                population=(
                    Leave.LeaveType.ANNUAL,
                    Leave.LeaveType.SICK,
                    Leave.LeaveType.UNPAID,
                ),
                weights=(80, 15, 5),
                k=1,
            )[0]
            Leave.objects.create(
                employee=employee,
                approver=employee.leave_approver or employee.manager,
                start_date=start,
                end_date=end,
                leave_type=leave_type,
                status=status,
                comment=SAMPLE_COMMENT,
                cancellation_reason=(
                    "Sample cancellation reason." if status == Leave.Status.CANCELED else ""
                ),
                canceled_at=(timezone.now() if status == Leave.Status.CANCELED else None),
            )
            created_count += 1

        return created_count

    def _add_workdays(self, start: datetime.date, days: int) -> datetime.date:
        result = start
        remaining = days
        while remaining:
            result += datetime.timedelta(days=1)
            if result.weekday() < 5:
                remaining -= 1
        return result
