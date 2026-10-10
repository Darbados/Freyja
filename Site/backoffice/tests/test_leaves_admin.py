import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Freyja.test_utils import force_two_factor_login
from employment.models import Employee
from leaves.models import Leave
from users.models import FreyjaUser


class BackofficeLeaveApiTests(TestCase):
    def setUp(self) -> None:
        self.staff_user = self._create_user("staff-leaves@example.com", is_staff=True)
        self.employee_user = self._create_user("employee-leaves@example.com")
        self.employee = Employee.objects.create(user=self.employee_user)
        self.leave = Leave.objects.create(
            employee=self.employee,
            start_date=datetime.date(2026, 8, 20),
            end_date=datetime.date(2026, 8, 21),
            comment="Family trip",
        )

    def test_requires_a_staff_user(self) -> None:
        url = reverse("api_backoffice_leaves")

        anonymous_response = self.client.get(url)
        force_two_factor_login(self.client, self.employee_user)
        employee_response = self.client.get(url)

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(employee_response.status_code, 403)

    def test_lists_leave_request_observability_fields(self) -> None:
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("api_backoffice_leaves"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        result = response.json()["results"][0]
        self.assertEqual(result["employee"]["email"], self.employee_user.email)
        self.assertEqual(result["status_label"], "Pending")
        self.assertEqual(result["leave_type_label"], "Annual")
        self.assertEqual(result["duration_days"], "2.00")
        self.assertEqual(result["comment"], "Family trip")
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)

    def test_paginates_fifty_requests_in_newest_first_order(self) -> None:
        Leave.objects.bulk_create(
            Leave(
                employee=self.employee,
                start_date=datetime.date(2026, 9, 1) + datetime.timedelta(days=number),
                end_date=datetime.date(2026, 9, 1) + datetime.timedelta(days=number),
                created_at=timezone.now() + datetime.timedelta(seconds=number),
            )
            for number in range(50)
        )
        force_two_factor_login(self.client, self.staff_user)

        first_page = self.client.get(reverse("api_backoffice_leaves"))
        second_page = self.client.get(reverse("api_backoffice_leaves"), {"page": 2})

        self.assertEqual(first_page.json()["count"], 51)
        self.assertEqual(len(first_page.json()["results"]), 50)
        self.assertEqual(len(second_page.json()["results"]), 1)

    @staticmethod
    def _create_user(email: str, *, is_staff: bool = False) -> FreyjaUser:
        return FreyjaUser.objects.create_user(
            username=email,
            email=email,
            password="test-password",
            is_staff=is_staff,
        )

    def test_detail_requires_staff(self) -> None:
        url = reverse("api_backoffice_leave_detail", args=(self.leave.pk,))
        self.assertEqual(self.client.get(url).status_code, 403)
        force_two_factor_login(self.client, self.employee_user)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_detail_includes_review_and_cancellation_metadata(self) -> None:
        approver = Employee.objects.create(user=self.staff_user)
        self.leave.approver = approver
        self.leave.reviewed_by = self.staff_user
        self.leave.reviewed_at = timezone.now()
        self.leave.canceled_at = timezone.now()
        self.leave.status = Leave.Status.CANCELED
        self.leave.cancellation_reason = "Plans changed"
        self.leave.save()
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("api_backoffice_leave_detail", args=(self.leave.pk,)))

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["approver"]["id"], self.staff_user.pk)
        self.assertEqual(result["reviewed_by"]["id"], self.staff_user.pk)
        self.assertEqual(result["cancellation_reason"], "Plans changed")
        self.assertEqual(result["status_label"], "Canceled")
        self.assertIsNotNone(result["reviewed_at"])
        self.assertIsNotNone(result["canceled_at"])

    def test_detail_handles_unassigned_request_and_missing_request(self) -> None:
        force_two_factor_login(self.client, self.staff_user)
        result = self.client.get(
            reverse("api_backoffice_leave_detail", args=(self.leave.pk,))
        ).json()
        self.assertIsNone(result["approver"])
        self.assertIsNone(result["reviewed_by"])
        self.assertEqual(
            self.client.get(reverse("api_backoffice_leave_detail", args=(999999,))).status_code,
            404,
        )

    def test_admin_endpoints_are_read_only(self) -> None:
        force_two_factor_login(self.client, self.staff_user)
        for url in (
            reverse("api_backoffice_leaves"),
            reverse("api_backoffice_leave_detail", args=(self.leave.pk,)),
        ):
            for method in ("post", "patch", "delete"):
                with self.subTest(url=url, method=method):
                    self.assertEqual(getattr(self.client, method)(url).status_code, 405)
