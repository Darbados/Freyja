from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employment.models import Employee
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
        self.client.force_login(self.employee.user)

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
            start += timedelta(days=1)
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

    def _next_weekday(self):
        day = timezone.localdate() + timedelta(days=1)
        while day.weekday() >= 5:
            day += timedelta(days=1)
        return day

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
