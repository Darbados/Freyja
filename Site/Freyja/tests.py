import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from Freyja.mailer import Mailer


class MailerTests(SimpleTestCase):
    @patch("Freyja.mailer.send_mail")
    def test_sends_leave_request_email(self, send_mail) -> None:
        leave = self._leave()

        Mailer().send_leave_request(leave)

        send_mail.assert_called_once_with(
            subject="Leave request from Emma Employee",
            message=(
                "Emma Employee submitted a leave request.\n\n"
                "Period: 10 Aug 2026 (Full day) – 11 Aug 2026 (Full day)\n"
                "Duration: 2 days\n"
                "Type: Annual\n"
                "Comment: Family appointment\n"
            ),
            from_email="webmaster@localhost",
            recipient_list=["manager@example.com"],
            html_message=None,
            fail_silently=False,
        )

    @patch("Freyja.mailer.send_mail")
    def test_sends_leave_cancellation_email(self, send_mail) -> None:
        leave = self._leave()

        Mailer().send_leave_cancellation(leave)

        send_mail.assert_called_once_with(
            subject="Leave request canceled by Emma Employee",
            message=(
                "Emma Employee canceled their leave request.\n\n"
                "Period: 10 Aug 2026 – 11 Aug 2026\n"
                "Duration: 2 days\n"
                "Cancellation reason: Plans changed\n"
            ),
            from_email="webmaster@localhost",
            recipient_list=["manager@example.com"],
            html_message=None,
            fail_silently=False,
        )

    @patch("Freyja.mailer.send_mail")
    @patch("Freyja.mailer.loader.render_to_string")
    def test_sends_forgotten_password_email(self, render_to_string, send_mail) -> None:
        render_to_string.side_effect = ["Reset your password\n", "Reset instructions"]

        Mailer().send_forgotten_password(
            context={"token": "token"},
            recipient="employee@example.com",
        )

        self.assertEqual(
            render_to_string.call_args_list[0].args[0],
            "registration/password_reset_subject.txt",
        )
        self.assertEqual(
            render_to_string.call_args_list[1].args[0],
            "registration/password_reset_email.txt",
        )

        send_mail.assert_called_once_with(
            subject="Reset your password",
            message="Reset instructions",
            from_email="webmaster@localhost",
            recipient_list=["employee@example.com"],
            html_message=None,
            fail_silently=True,
        )

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
