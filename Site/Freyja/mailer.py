from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import loader


class Mailer:
    """Defines and delivers all application emails."""

    def send_leave_request(self, leave: Any) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        self._send(
            subject=f"Leave request from {requester_name}",
            message=loader.render_to_string(
                "emails/leave_request.txt",
                {
                    "leave": leave,
                    "requester_name": requester_name,
                    "comment": leave.comment or "No comment provided.",
                },
            ),
            recipient=leave.approver.user.email,
        )

    def send_leave_cancellation(self, leave: Any) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        self._send(
            subject=f"Leave request canceled by {requester_name}",
            message=loader.render_to_string(
                "emails/leave_cancellation.txt",
                {"leave": leave, "requester_name": requester_name},
            ),
            recipient=leave.approver.user.email,
        )

    def send_forgotten_password(
        self,
        *,
        context: dict[str, Any],
        recipient: str,
        from_email: str | None = None,
    ) -> None:
        subject = "".join(
            loader.render_to_string("registration/password_reset_subject.txt", context).splitlines()
        )
        self._send(
            subject=subject,
            message=loader.render_to_string("registration/password_reset_email.txt", context),
            recipient=recipient,
            from_email=from_email,
            fail_silently=True,
        )

    def _send(
        self,
        *,
        subject: str,
        message: str,
        recipient: str,
        from_email: str | None = None,
        html_message: str | None = None,
        fail_silently: bool = False,
    ) -> None:
        message_options = {
            "subject": subject,
            "body": message,
            "from_email": from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
            "to": [recipient],
        }
        if html_message is None:
            email = EmailMessage(**message_options)
        else:
            email = EmailMultiAlternatives(**message_options)
            email.attach_alternative(html_message, "text/html")

        email.send(fail_silently=fail_silently)
