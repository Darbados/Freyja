import datetime
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO, StringIO
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from pypdf import PdfReader

from employment.models import Employee, Employer, Employment, EmploymentType, RelationshipKind
from Freyja.test_utils import force_two_factor_login
from leaves.balance import _leave_days_in_period
from leaves.calendar import is_working_day, working_dates
from leaves.documents import create_leave_request, generate_document
from leaves.models import Leave, LeaveDocument
from users.models import FreyjaUser


def fixture():
    manager = Employee.objects.create(
        user=FreyjaUser.objects.create_user(username="manager", email="manager@example.com")
    )
    employee = Employee.objects.create(
        user=FreyjaUser.objects.create_user(username="employee", email="employee@example.com"),
        manager=manager,
        legal_name="Мария Петрова Иванова",
        personnel_number="EMP-42",
        job_title="Софтуерен инженер",
    )
    employer = Employer.objects.create(legal_name="Пример ООД", eik="123456789")
    kind = EmploymentType.objects.create(
        name="Employment", code="employment", relationship_kind=RelationshipKind.EMPLOYMENT
    )
    employment = Employment.objects.create(
        employee=employee,
        employment_type=kind,
        employer=employer,
        start_date=datetime.date(2020, 1, 1),
        uses_bulgarian_leave_calendar=True,
    )
    return employee, manager, employment


class LeaveDocumentTests(TestCase):
    def setUp(self):
        self.employee, self.manager, self.employment = fixture()
        force_two_factor_login(self.client, self.employee.user)
        self.payload = {
            "start_date": "2026-12-23",
            "end_date": "2026-12-29",
            "leave_type": 1,
            "client_request_id": str(uuid.uuid4()),
            "comment": "Private internal comment",
        }

    def create(self, **changes):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                reverse("leave_requests"), self.payload | changes, content_type="application/json"
            )

    def test_generates_cyrillic_pdf_and_freezes_exact_days(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.content)
        document = LeaveDocument.objects.get()
        self.assertEqual(document.state, "ready")
        self.assertEqual(document.snapshot["working_dates"], ["2026-12-23", "2026-12-29"])
        self.assertEqual(document.snapshot["working_days"], 2)
        self.assertEqual(document.sha256, hashlib.sha256(bytes(document.pdf)).hexdigest())
        pdf = PdfReader(BytesIO(bytes(document.pdf)))
        self.assertEqual(len(pdf.pages), 1)
        text = pdf.pages[0].extract_text()
        for value in ["Мария Петрова Иванова", "Пример ООД", "23.12.2026", "2 работни дни"]:
            self.assertIn(value, text)
        self.assertNotIn("Private internal comment", text)
        self.assertNotIn("comment", document.snapshot)
        self.assertEqual(len(mail.outbox), 1)

    def test_estimate_uses_submission_calendar_without_creating_records(self):
        response = self.client.post(
            reverse("leave_estimate"), self.payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"duration_days": "2", "duration_hours": "16"})
        self.assertFalse(Leave.objects.exists())
        invalid = self.payload | {"start_day_part": "second_half"}
        self.assertEqual(
            self.client.post(
                reverse("leave_estimate"), invalid, content_type="application/json"
            ).status_code,
            400,
        )

    def test_backoffice_only_exposes_metadata_to_document_readers(self):
        self.create()
        document = LeaveDocument.objects.get()
        staff = FreyjaUser.objects.create_user(username="hr", email="hr@example.com", is_staff=True)
        force_two_factor_login(self.client, staff)
        path = f"/api/backoffice/leaves/{document.leave_id}"
        self.assertIsNone(self.client.get(path).json()["document"])
        staff.user_permissions.add(Permission.objects.get(codename="access_leave_documents"))
        self.assertEqual(self.client.get(path).json()["document"]["state"], "ready")

    def test_original_pdf_survives_profile_changes_and_retries(self):
        self.create()
        document = LeaveDocument.objects.get()
        original = bytes(document.pdf)
        self.employee.legal_name = "Changed name"
        self.employee.save()
        self.employment.employer.legal_name = "Changed company"
        self.employment.employer.save()
        generate_document(document.pk)
        document.refresh_from_db()
        self.assertEqual(bytes(document.pdf), original)
        self.assertEqual(document.attempts, 1)

    def test_duplicate_submission_returns_same_request_and_does_not_send_again(self):
        first = self.create()
        second = self.create()
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(Leave.objects.count(), 1)
        self.assertEqual(LeaveDocument.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(second.json()["document"]["state"], "ready")

    def test_duplicate_key_with_changed_data_conflicts(self):
        self.create()
        response = self.create(end_date="2026-12-30")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Leave.objects.count(), 1)

    def test_failure_persists_request_and_retries_the_original_snapshot(self):
        with patch("leaves.documents.render_annual_request", side_effect=RuntimeError("renderer")):
            with self.assertLogs("leaves.documents", level="ERROR"):
                response = self.create()
        self.assertEqual(response.status_code, 201)
        document = LeaveDocument.objects.get()
        self.assertEqual(document.state, "failed")
        self.employee.legal_name = "Changed name"
        self.employee.save()
        response = self.client.post(reverse("leave_document_retry", args=[document.leave_id]))
        self.assertEqual(response.json()["state"], "ready")
        document.refresh_from_db()
        self.assertEqual(document.attempts, 2)
        self.assertIn(
            "Мария Петрова Иванова", PdfReader(BytesIO(bytes(document.pdf))).pages[0].extract_text()
        )

    def test_command_recovers_job_not_started_after_commit(self):
        response = self.client.post(
            reverse("leave_requests"), self.payload, content_type="application/json"
        )
        self.assertEqual(response.json()["document"]["state"], "pending")
        document = LeaveDocument.objects.get()
        self.assertEqual(
            self.client.get(reverse("leave_document_pdf", args=[document.leave_id])).status_code,
            409,
        )
        call_command("generate_leave_documents", stdout=StringIO())
        document.refresh_from_db()
        self.assertEqual(document.state, "ready")

    def test_access_requires_owner_assigned_approver_or_document_permission(self):
        self.create()
        document = LeaveDocument.objects.get()
        path = reverse("leave_document_pdf", args=[document.leave_id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertTrue(response["Content-Disposition"].startswith("inline;"))
        self.assertTrue(
            self.client.get(path, {"download": "1"})["Content-Disposition"].startswith(
                "attachment;"
            )
        )
        force_two_factor_login(self.client, self.manager.user)
        self.assertEqual(self.client.get(path).status_code, 200)
        outsider = FreyjaUser.objects.create_user(
            username="outsider", email="other@example.com", is_staff=True
        )
        force_two_factor_login(self.client, outsider)
        for endpoint in ("leave_document", "leave_document_pdf"):
            self.assertEqual(
                self.client.get(reverse(endpoint, args=[document.leave_id])).status_code, 404
            )
        self.assertEqual(
            self.client.post(reverse("leave_document_retry", args=[document.leave_id])).status_code,
            404,
        )
        outsider.user_permissions.add(Permission.objects.get(codename="access_leave_documents"))
        self.assertEqual(self.client.get(path).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(path).status_code, 403)

    def test_missing_profile_data_does_not_create_a_request(self):
        self.employee.legal_name = ""
        self.employee.save()
        response = self.create()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Leave.objects.exists())
        self.assertFalse(LeaveDocument.objects.exists())

    def test_unsupported_employment_rejected(self):
        for field, value in [
            ("uses_bulgarian_leave_calendar", False),
            ("employer", None),
            ("end_date", datetime.date(2026, 12, 24)),
        ]:
            original = getattr(self.employment, field)
            setattr(self.employment, field, value)
            self.employment.save()
            self.assertEqual(self.create().status_code, 400, field)
            setattr(self.employment, field, original)
            self.employment.save()
        self.employment.employment_type.relationship_kind = RelationshipKind.CIVIL
        self.employment.employment_type.save()
        self.assertEqual(self.create().status_code, 400)

    def test_overlapping_employments_rejected_instead_of_guessing(self):
        self.employment.pk = None
        self.employment.save()
        self.assertEqual(self.create().status_code, 400)

    def test_rejects_half_days_holidays_and_excessive_ranges(self):
        for change in [
            {"start_day_part": "second_half"},
            {"start_date": "2026-12-24"},
            {"start_date": "2026-09-07", "end_date": "2026-09-08"},
            {"end_date": "2030-12-30"},
        ]:
            self.assertEqual(self.create(**change).status_code, 400, change)
        self.assertFalse(Leave.objects.exists())

    def test_legacy_and_non_annual_requests_have_no_document(self):
        response = self.create(leave_type=2)
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()["document"])
        self.assertFalse(LeaveDocument.objects.exists())

    def test_document_prevents_destructive_edits_and_employee_deletion(self):
        self.create()
        document = LeaveDocument.objects.get()
        leave = document.leave
        leave.end_date = datetime.date(2026, 12, 30)
        with self.assertRaises(ValidationError):
            leave.save()
        with self.assertRaises(ProtectedError):
            self.employee.delete()
        document.snapshot = {}
        with self.assertRaises(ValidationError):
            document.save()

    def test_cancellation_preserves_document(self):
        self.create()
        document = LeaveDocument.objects.get()
        original = bytes(document.pdf)
        with patch("leaves.views.timezone.localdate", return_value=datetime.date(2026, 10, 12)):
            response = self.client.post(
                reverse("leave_request_cancel", args=[document.leave_id]),
                {"reason": "Plans changed"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200, response.content)
        document.refresh_from_db()
        self.assertEqual(bytes(document.pdf), original)

    def test_long_text_and_markup_are_rendered_as_text(self):
        self.employee.legal_name = "Мария <img src='https://invalid.example/a'> & Иванова " * 4
        self.employee.job_title = "Старши инженер по разработка и проверка на системи " * 4
        self.employee.save()
        self.assertEqual(self.create().status_code, 201)
        document = LeaveDocument.objects.get()
        self.assertEqual(document.state, "ready")
        text = " ".join(
            page.extract_text() for page in PdfReader(BytesIO(bytes(document.pdf))).pages
        )
        self.assertIn("<img", text)
        self.assertIn("Подпис на служителя", text)


class BulgarianCalendarTests(TestCase):
    def test_easter_substitute_and_cross_year_holidays(self):
        for day in [
            datetime.date(2026, 4, 10),
            datetime.date(2026, 4, 13),
            datetime.date(2026, 9, 7),
            datetime.date(2026, 12, 28),
            datetime.date(2027, 1, 1),
        ]:
            self.assertFalse(is_working_day(day), day)
        self.assertEqual(
            working_dates(datetime.date(2026, 12, 30), datetime.date(2027, 1, 4)),
            [datetime.date(2026, 12, 30), datetime.date(2026, 12, 31), datetime.date(2027, 1, 4)],
        )

    def test_balance_and_request_totals_use_same_calendar(self):
        leave = Leave(start_date=datetime.date(2026, 12, 23), end_date=datetime.date(2026, 12, 29))
        self.assertEqual(leave.duration_days, 2)
        self.assertEqual(_leave_days_in_period(leave, leave.start_date, leave.end_date), 2)


class ConcurrentDocumentTests(TransactionTestCase):
    def test_concurrent_workers_publish_one_pdf(self):
        employee, _, _ = fixture()
        with patch("leaves.documents.transaction.on_commit"):
            leave, _ = create_leave_request(
                employee.pk,
                {
                    "start_date": datetime.date(2026, 10, 19),
                    "end_date": datetime.date(2026, 10, 23),
                    "leave_type": 1,
                },
            )
        document_id = leave.document.pk
        barrier = Barrier(2)

        def render():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return generate_document(document_id).sha256
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            hashes = list(pool.map(lambda _: render(), range(2)))
        self.assertEqual(hashes[0], hashes[1])
        self.assertEqual(LeaveDocument.objects.get().attempts, 1)

    def test_duplicate_submissions_and_render_jobs_are_serialized(self):
        employee, _, _ = fixture()
        data = {
            "start_date": datetime.date(2026, 10, 19),
            "end_date": datetime.date(2026, 10, 23),
            "client_request_id": uuid.uuid4(),
            "leave_type": 1,
        }
        barrier = Barrier(2)

        def submit():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return create_leave_request(employee.pk, data)[0].pk
            finally:
                close_old_connections()

        with patch("leaves.documents.Mailer.send_leave_request") as notification:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: submit(), range(2)))
            self.assertEqual(notification.call_count, 1)
        self.assertEqual(results[0], results[1])
        document = LeaveDocument.objects.get()
        self.assertEqual(document.state, "ready")
        self.assertEqual(document.attempts, 1)
