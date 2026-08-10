from unittest.mock import patch

from django.core import signing
from django.test import TestCase, override_settings
from django.urls import reverse

from authentication.email_confirmation import EmailConfirmationSigner
from users.models import FreyjaUser


class PasswordResetApiTests(TestCase):
    @patch("authentication.forms.Mailer")
    def test_delegates_email_delivery_to_mailer(self, mailer_class) -> None:
        user = FreyjaUser.objects.create_user(
            username="employee@example.com",
            email="employee@example.com",
            password="test-password",
        )

        response = self.client.post(
            reverse("api_auth_password_reset"),
            {"email": user.email},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        call = mailer_class.return_value.send_forgotten_password.call_args
        self.assertEqual(call.kwargs["recipient"], user.email)
        self.assertEqual(call.kwargs["context"]["user"], user)


class AccountConfirmationTests(TestCase):
    @patch("authentication.views.Mailer")
    def test_registration_sends_a_signed_confirmation_link(self, mailer_class) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("api_auth_register"),
                {
                    "first_name": "Emma",
                    "last_name": "Employee",
                    "email": "employee@example.com",
                    "password": "unique-secure-password-938!",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        user = FreyjaUser.objects.get(email="employee@example.com")
        call = mailer_class.return_value.send_account_confirmation.call_args
        self.assertEqual(call.args[0], user)
        token = call.args[1].rsplit("/", 1)[-1]
        self.assertEqual(EmailConfirmationSigner().verify_token(token), user)

    def test_signed_link_confirms_the_matching_email(self) -> None:
        user = self._user()
        token = EmailConfirmationSigner().create_token(user)

        response = self.client.get(reverse("api_auth_confirm_email", args=(token,)))

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertIsNotNone(user.email_confirmed_at)

    def test_confirmation_is_idempotent(self) -> None:
        user = self._user()
        token = EmailConfirmationSigner().create_token(user)
        self.client.get(reverse("api_auth_confirm_email", args=(token,)))
        user.refresh_from_db()
        confirmed_at = user.email_confirmed_at

        response = self.client.get(reverse("api_auth_confirm_email", args=(token,)))

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email_confirmed_at, confirmed_at)

    def test_tampered_link_is_rejected(self) -> None:
        token = EmailConfirmationSigner().create_token(self._user())

        response = self.client.get(reverse("api_auth_confirm_email", args=(f"{token}tampered",)))

        self.assertEqual(response.status_code, 400)

    @override_settings(EMAIL_CONFIRMATION_TIMEOUT=-1)
    def test_expired_link_is_rejected(self) -> None:
        token = EmailConfirmationSigner().create_token(self._user())

        response = self.client.get(reverse("api_auth_confirm_email", args=(token,)))

        self.assertEqual(response.status_code, 400)

    def test_link_is_rejected_after_email_changes(self) -> None:
        user = self._user()
        token = EmailConfirmationSigner().create_token(user)
        user.email = "changed@example.com"
        user.username = user.email
        user.save(update_fields=("email", "username", "updated_at"))

        with self.assertRaises(signing.BadSignature):
            EmailConfirmationSigner().verify_token(token)

    @staticmethod
    def _user() -> FreyjaUser:
        return FreyjaUser.objects.create_user(
            username="employee@example.com",
            email="employee@example.com",
            password="test-password",
        )
