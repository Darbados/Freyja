from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader


class Mailer:
    """Defines and delivers all application emails."""

    def send_leave_request(self, leave: Any) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        start = f"{leave.start_date:%d %b %Y} ({leave.get_start_day_part_display()})"
        end = f"{leave.end_date:%d %b %Y} ({leave.get_end_day_part_display()})"
        comment = leave.comment or "No comment provided."
        self._send(
            subject=f"Leave request from {requester_name}",
            message=(
                f"{requester_name} submitted a leave request.\n\n"
                f"Period: {start} – {end}\n"
                f"Duration: {leave.duration_days} days\n"
                f"Type: {leave.get_leave_type_display()}\n"
                f"Comment: {comment}"
            ),
            recipient=leave.approver.user.email,
        )

    def send_leave_cancellation(self, leave: Any) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        self._send(
            subject=f"Leave request canceled by {requester_name}",
            message=(
                f"{requester_name} canceled their leave request.\n\n"
                f"Period: {leave.start_date:%d %b %Y} – {leave.end_date:%d %b %Y}\n"
                f"Duration: {leave.duration_days} days\n"
                f"Cancellation reason: {leave.cancellation_reason}"
            ),
            recipient=leave.approver.user.email,
        )

    def send_forgotten_password(
        self,
        *,
        subject_template_name: str,
        email_template_name: str,
        context: dict[str, Any],
        recipient: str,
        from_email: str | None = None,
        html_email_template_name: str | None = None,
    ) -> None:
        subject = "".join(loader.render_to_string(subject_template_name, context).splitlines())
        message = loader.render_to_string(email_template_name, context)
        html_message = (
            loader.render_to_string(html_email_template_name, context)
            if html_email_template_name
            else None
        )
        self._send(
            subject=subject,
            message=message,
            recipient=recipient,
            from_email=from_email,
            html_message=html_message,
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
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=fail_silently,
        )
