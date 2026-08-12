import datetime
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Freyja.test_utils import force_two_factor_login
from employment.models import Employee, Employment, EmploymentType, RelationshipKind
from departments.models import Department, DepartmentEmployee
from leaves.models import Leave
from users.models import FreyjaUser


class LeaveRequestApiTests(TestCase):
    def setUp(self) -> None:
        self.manager = self._employee("manager@example.com", "Maya", "Manager")
        self.employee = self._employee(
            "employee@example.com",
            "Emma",
            "Employee",
            manager=self.manager,
        )
        force_two_factor_login(self.client, self.employee.user)

    def test_creates_leave_and_emails_the_manager(self) -> None:
        start = self._next_weekday()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("leave_requests"),
                {
                    "start_date": start.isoformat(),
                    "end_date": start.isoformat(),
                    "start_day_part": Leave.DayPart.SECOND_HALF,
                    "end_day_part": Leave.DayPart.SECOND_HALF,
                    "leave_type": Leave.LeaveType.ANNUAL,
                    "comment": "Family appointment",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        leave = Leave.objects.get()
        self.assertEqual(leave.employee, self.employee)
        self.assertEqual(leave.approver, self.manager)
        self.assertEqual(leave.duration_hours, 4)
        self.assertEqual(leave.duration_days, 0.5)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.manager.user.email])
        self.assertIn("Family appointment", mail.outbox[0].body)

    def test_prefers_the_assigned_leave_approver(self) -> None:
        approver = self._employee("approver@example.com", "Ava", "Approver")
        self.employee.leave_approver = approver
        self.employee.save()
        start = self._next_weekday()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("leave_requests"),
                {
                    "start_date": start.isoformat(),
                    "end_date": start.isoformat(),
                    "start_day_part": Leave.DayPart.FULL_DAY,
                    "end_day_part": Leave.DayPart.FULL_DAY,
                    "leave_type": Leave.LeaveType.ANNUAL,
                    "comment": "",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Leave.objects.get().approver, approver)
        self.assertEqual(mail.outbox[0].to, [approver.user.email])

    def test_rejects_a_weekend_leave_boundary(self) -> None:
        start = timezone.localdate()
        while start.weekday() != 5:
            start += datetime.timedelta(days=1)
        response = self.client.post(
            reverse("leave_requests"),
            {
                "start_date": start.isoformat(),
                "end_date": start.isoformat(),
                "start_day_part": Leave.DayPart.FIRST_HALF,
                "end_day_part": Leave.DayPart.FIRST_HALF,
                "leave_type": Leave.LeaveType.ANNUAL,
                "comment": "",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Leave.objects.exists())

    def test_lists_only_the_signed_in_employees_requests(self) -> None:
        start = self._next_weekday()
        Leave.objects.create(
            employee=self.employee,
            approver=self.manager,
            start_date=start,
            end_date=start,
        )
        other = self._employee("other@example.com", "Other", "Employee")
        Leave.objects.create(
            employee=other,
            start_date=start,
            end_date=start,
        )

        response = self.client.get(reverse("leave_requests"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["leave_requests"]), 1)

    def test_cancels_an_owned_active_request_and_emails_the_approver(self) -> None:
        leave = self._leave(self.employee, self._next_weekday(), approver=self.manager)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("leave_request_cancel", args=(leave.id,)),
                {"reason": "Plans changed"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        leave.refresh_from_db()
        self.assertEqual(leave.status, Leave.Status.CANCELED)
        self.assertEqual(leave.cancellation_reason, "Plans changed")
        self.assertIsNotNone(leave.canceled_at)
        self.assertFalse(response.json()["can_cancel"])
        self.assertEqual(mail.outbox[0].to, [self.manager.user.email])
        self.assertIn("Plans changed", mail.outbox[0].body)

    def test_requires_a_cancellation_reason(self) -> None:
        leave = self._leave(self.employee, self._next_weekday(), approver=self.manager)

        response = self.client.post(
            reverse("leave_request_cancel", args=(leave.id,)),
            {"reason": "   "},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        leave.refresh_from_db()
        self.assertEqual(leave.status, Leave.Status.PENDING)

    def test_cannot_cancel_another_employees_request(self) -> None:
        other = self._employee("another@example.com", "Another", "Employee")
        leave = self._leave(other, self._next_weekday())

        response = self.client.post(
            reverse("leave_request_cancel", args=(leave.id,)),
            {"reason": "Not mine"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_cannot_cancel_a_request_after_its_period_ended(self) -> None:
        day = timezone.localdate() - datetime.timedelta(days=1)
        while day.weekday() >= 5:
            day -= datetime.timedelta(days=1)
        leave = self._leave(self.employee, day, approver=self.manager)

        response = self.client.post(
            reverse("leave_request_cancel", args=(leave.id,)),
            {"reason": "Too late"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        leave.refresh_from_db()
        self.assertEqual(leave.status, Leave.Status.PENDING)

    def test_returns_the_current_annual_leave_balance(self) -> None:
        year = timezone.localdate().year
        employment_type = EmploymentType.objects.create(
            name="Full time",
            code="full-time",
            relationship_kind=RelationshipKind.EMPLOYMENT,
            default_base_leave_days=Decimal("20"),
        )
        Employment.objects.create(
            employee=self.employee,
            employment_type=employment_type,
            start_date=datetime.date(year, 1, 1),
        )
        full_day = self._next_weekday()
        half_day = full_day + datetime.timedelta(days=1)
        if half_day.weekday() >= 5:
            half_day += datetime.timedelta(days=7 - half_day.weekday())
        self._leave(self.employee, full_day, approver=self.manager)
        for _ in range(6):
            self._leave(self.employee, full_day, approver=self.manager)
        Leave.objects.create(
            employee=self.employee,
            approver=self.manager,
            start_date=half_day,
            end_date=half_day,
            start_day_part=Leave.DayPart.FIRST_HALF,
            end_day_part=Leave.DayPart.FIRST_HALF,
            status=Leave.Status.APPROVED,
        )
        ignored = self._leave(self.employee, full_day, approver=self.manager)
        ignored.status = Leave.Status.CANCELED
        ignored.cancellation_reason = "Canceled"
        ignored.save()

        response = self.client.get(reverse("leave_requests"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["annual_leave_balance"],
            {
                "year": year,
                "entitlement_days": 20,
                "booked_days": "7.50",
                "remaining_days": "12.50",
            },
        )

    def test_prorates_the_starting_year_by_month_and_rounds_up(self) -> None:
        year = timezone.localdate().year
        employment_type = EmploymentType.objects.create(
            name="Mid-year full time",
            code="mid-year-full-time",
            relationship_kind=RelationshipKind.EMPLOYMENT,
            default_base_leave_days=Decimal("20"),
        )
        Employment.objects.create(
            employee=self.employee,
            employment_type=employment_type,
            start_date=datetime.date(year, 8, 1),
        )

        response = self.client.get(reverse("leave_requests"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["annual_leave_balance"]["entitlement_days"],
            9,
        )

    def test_treats_an_override_as_the_final_entitlement_and_rounds_up(self) -> None:
        year = timezone.localdate().year
        employment_type = EmploymentType.objects.create(
            name="Overridden full time",
            code="overridden-full-time",
            relationship_kind=RelationshipKind.EMPLOYMENT,
            default_base_leave_days=Decimal("20"),
        )
        Employment.objects.create(
            employee=self.employee,
            employment_type=employment_type,
            start_date=datetime.date(year, 8, 1),
            base_leave_days_override=Decimal("12.25"),
        )

        response = self.client.get(reverse("leave_requests"))

        self.assertEqual(
            response.json()["annual_leave_balance"]["entitlement_days"],
            13,
        )

    def test_manager_lists_all_direct_report_leave_requests(self) -> None:
        leave = self._leave(self.employee, self._next_weekday(), approver=self.manager)
        other_manager = self._employee("other-manager@example.com", "Other", "Manager")
        other_employee = self._employee(
            "outside@example.com",
            "Outside",
            "Employee",
            manager=other_manager,
        )
        self._leave(other_employee, self._next_weekday(), approver=other_manager)
        force_two_factor_login(self.client, self.manager.user)

        response = self.client.get(reverse("team_leave_requests"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_manager"])
        self.assertEqual(len(response.json()["leave_requests"]), 1)
        self.assertEqual(response.json()["leave_requests"][0]["id"], leave.id)
        self.assertEqual(
            response.json()["leave_requests"][0]["employee"]["email"],
            self.employee.user.email,
        )

    def test_non_manager_has_no_team_tab_data(self) -> None:
        response = self.client.get(reverse("team_leave_requests"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_manager"])
        self.assertEqual(response.json()["leave_requests"], [])

    def test_department_schedule_contains_only_approved_colleague_leave(self) -> None:
        department = Department.objects.create(name="Technology", director=self.manager.user)
        DepartmentEmployee.objects.create(department=department, user=self.employee.user)
        colleague = self._employee("colleague@example.com", "Team", "Colleague")
        DepartmentEmployee.objects.create(department=department, user=colleague.user)
        approved = self._leave(colleague, self._next_weekday(), approver=self.manager)
        approved.status = Leave.Status.APPROVED
        approved.comment = "Private appointment details"
        approved.save()
        pending = self._leave(colleague, self._next_weekday(), approver=self.manager)

        response = self.client.get(reverse("department_leave_schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["departments"], [{"id": department.id, "name": "Technology"}]
        )
        self.assertEqual(len(response.json()["leave_requests"]), 1)
        self.assertEqual(response.json()["leave_requests"][0]["id"], approved.id)
        self.assertNotEqual(response.json()["leave_requests"][0]["id"], pending.id)
        self.assertNotIn("comment", response.json()["leave_requests"][0])

    def test_department_schedule_contains_only_the_requested_month(self) -> None:
        department = Department.objects.create(name="Technology", director=self.manager.user)
        DepartmentEmployee.objects.create(department=department, user=self.employee.user)
        colleague = self._employee("colleague@example.com", "Team", "Colleague")
        DepartmentEmployee.objects.create(department=department, user=colleague.user)
        month_start = datetime.date(2026, 8, 1)
        current = self._leave(colleague, datetime.date(2026, 8, 3), approver=self.manager)
        current.end_date = datetime.date(2026, 8, 7)
        current.status = Leave.Status.APPROVED
        current.save()
        historical = self._leave(colleague, datetime.date(2026, 7, 31), approver=self.manager)
        historical.status = Leave.Status.APPROVED
        historical.save()
        distant = self._leave(colleague, datetime.date(2026, 9, 1), approver=self.manager)
        distant.status = Leave.Status.APPROVED
        distant.save()

        response = self.client.get(reverse("department_leave_schedule"), {"month": "2026-08"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["window_start"], month_start.isoformat())
        self.assertEqual(
            response.json()["window_end"],
            datetime.date(2026, 8, 31).isoformat(),
        )
        self.assertEqual(
            [leave["id"] for leave in response.json()["leave_requests"]],
            [current.id],
        )

    def test_department_schedule_rejects_an_invalid_month(self) -> None:
        response = self.client.get(reverse("department_leave_schedule"), {"month": "August"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["month"], "Use the YYYY-MM format.")

    def _next_weekday(self):
        day = timezone.localdate() + datetime.timedelta(days=1)
        while day.weekday() >= 5:
            day += datetime.timedelta(days=1)
        return day

    def _leave(
        self,
        employee: Employee,
        day,
        approver: Employee | None = None,
    ) -> Leave:
        return Leave.objects.create(
            employee=employee,
            approver=approver,
            start_date=day,
            end_date=day,
        )

    def _employee(
        self,
        email: str,
        first_name: str,
        last_name: str,
        manager: Employee | None = None,
    ) -> Employee:
        user = FreyjaUser.objects.create_user(
            username=email,
            email=email,
            password="test-password",
            first_name=first_name,
            last_name=last_name,
        )
        return Employee.objects.create(user=user, manager=manager)
