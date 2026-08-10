import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from Freyja.mailer import Mailer


class MailerTests(SimpleTestCase):
    @patch("Freyja.mailer.EmailMessage")
    def test_sends_leave_request_email(self, email_message) -> None:
        leave = self._leave()

        Mailer().send_leave_request(leave)

        email_message.assert_called_once_with(
            subject="Leave request from Emma Employee",
            body=(
                "Emma Employee submitted a leave request.\n\n"
                "Period: 10 Aug 2026 (Full day) – 11 Aug 2026 (Full day)\n"
                "Duration: 2 days\n"
                "Type: Annual\n"
                "Comment: Family appointment\n"
            ),
            from_email="webmaster@localhost",
            to=["manager@example.com"],
        )
        email_message.return_value.send.assert_called_once_with()

    @patch("Freyja.mailer.EmailMessage")
    def test_sends_leave_cancellation_email(self, email_message) -> None:
        leave = self._leave()

        Mailer().send_leave_cancellation(leave)

        email_message.assert_called_once_with(
            subject="Leave request canceled by Emma Employee",
            body=(
                "Emma Employee canceled their leave request.\n\n"
                "Period: 10 Aug 2026 – 11 Aug 2026\n"
                "Duration: 2 days\n"
                "Cancellation reason: Plans changed\n"
            ),
            from_email="webmaster@localhost",
            to=["manager@example.com"],
        )
        email_message.return_value.send.assert_called_once_with()

    @patch("Freyja.mailer.EmailMessage")
    @patch("Freyja.mailer.loader.render_to_string")
    def test_sends_forgotten_password_email(self, render_to_string, email_message) -> None:
        render_to_string.return_value = "Reset instructions"

        Mailer().send_forgotten_password(
            context={"token": "token"},
            recipient="employee@example.com",
        )

        self.assertEqual(
            render_to_string.call_args_list[0].args[0],
            "registration/password_reset_email.txt",
        )

        email_message.assert_called_once_with(
            subject="Freyja password reset",
            body="Reset instructions",
            from_email="webmaster@localhost",
            to=["employee@example.com"],
        )
        email_message.return_value.send.assert_called_once_with()

    @staticmethod
    def _leave() -> SimpleNamespace:
        requester = SimpleNamespace(
            email="employee@example.com",
            get_full_name=lambda: "Emma Employee",
        )
        approver = SimpleNamespace(user=SimpleNamespace(email="manager@example.com"))
        return SimpleNamespace(
            employee=SimpleNamespace(user=requester),
            approver=approver,
            start_date=datetime.date(2026, 8, 10),
            end_date=datetime.date(2026, 8, 11),
            duration_days=2,
            comment="Family appointment",
            cancellation_reason="Plans changed",
            get_start_day_part_display=lambda: "Full day",
            get_end_day_part_display=lambda: "Full day",
            get_leave_type_display=lambda: "Annual",
        )
