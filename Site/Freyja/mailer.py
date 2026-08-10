from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import loader


class Mailer:
    """Defines and delivers all application emails."""

    def send_leave_request(self, leave: Any) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        self._send(
            EmailMessage(
                subject=f"Leave request from {requester_name}",
                body=loader.render_to_string(
                    "emails/leave_request.txt",
                    {
                        "leave": leave,
                        "requester_name": requester_name,
                        "comment": leave.comment or "No comment provided.",
                    },
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[leave.approver.user.email],
            )
        )

    def send_leave_cancellation(self, leave: Any) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        self._send(
            EmailMessage(
                subject=f"Leave request canceled by {requester_name}",
                body=loader.render_to_string(
                    "emails/leave_cancellation.txt",
                    {"leave": leave, "requester_name": requester_name},
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[leave.approver.user.email],
            )
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
            EmailMessage(
                subject=subject,
                body=loader.render_to_string("registration/password_reset_email.txt", context),
                from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[recipient],
            )
        )

    def _send(self, email: EmailMessage | EmailMultiAlternatives) -> None:
        email.send()
