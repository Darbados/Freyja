from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm

from Freyja.mailer import Mailer


class EmailAuthenticationForm(AuthenticationForm):
    """Represents an email-first login form."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )


class EmailPasswordResetForm(PasswordResetForm):
    """Represents a password reset form by email."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def send_mail(
        self,
        subject_template_name: str,
        email_template_name: str,
        context: dict[str, Any],
        from_email: str | None,
        to_email: str,
        html_email_template_name: str | None = None,
    ) -> None:
        Mailer().send_forgotten_password(
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            context=context,
            recipient=to_email,
            from_email=from_email,
            html_email_template_name=html_email_template_name,
        )
