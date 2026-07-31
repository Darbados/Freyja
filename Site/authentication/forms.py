from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm


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
