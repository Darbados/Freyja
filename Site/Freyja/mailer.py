from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import loader

if TYPE_CHECKING:
    from leaves.models import Leave as LeaveRequest
    from users.models import FreyjaUser


class Mailer:
    """Defines and delivers all application emails."""

    def send_leave_request(self, leave_request: LeaveRequest) -> None:
        requester_name = (
            leave_request.employee.user.get_full_name() or leave_request.employee.user.email
        )
        subject = f"Leave request from {requester_name}"
        msg = EmailMessage(
            subject=subject,
            body=loader.render_to_string(
                "emails/leave_request.txt",
                {
                    "leave": leave_request,
                    "requester_name": requester_name,
                    "comment": leave_request.comment or "No comment provided.",
                },
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[leave_request.approver.user.email],
        )
        self._send(msg)

    def send_leave_cancellation(self, leave_request: LeaveRequest) -> None:
        requester_name = (
            leave_request.employee.user.get_full_name() or leave_request.employee.user.email
        )
        subject = f"Leave request canceled by {requester_name}"
        msg = EmailMessage(
            subject=subject,
            body=loader.render_to_string(
                "emails/leave_cancellation.txt",
                {"leave": leave_request, "requester_name": requester_name},
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[leave_request.approver.user.email],
        )
        self._send(msg)

    def send_forgotten_password(
        self,
        *,
        context: dict[str, Any],
        recipient: str,
        from_email: str | None = None,
    ) -> None:
        subject = "Freyja password reset"
        msg = EmailMessage(
            subject=subject,
            body=loader.render_to_string("registration/password_reset_email.txt", context),
            from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[recipient],
        )
        self._send(msg)

    def send_account_confirmation(
        self,
        user: FreyjaUser,
        confirmation_url: str,
    ) -> None:
        subject = "Confirm your Freyja account"
        msg = EmailMessage(
            subject=subject,
            body=loader.render_to_string(
                "emails/account_confirmation.txt",
                {"user": user, "confirmation_url": confirmation_url},
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[user.email],
        )
        self._send(msg)

    def _send(self, msg: EmailMessage | EmailMultiAlternatives) -> None:
        msg.send()
