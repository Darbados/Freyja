from unittest.mock import patch

from django.core import signing
from django.test import TestCase, override_settings
from django.urls import reverse

from authentication.email_confirmation import EmailConfirmationSigner
from authentication.totp import code_at, decrypt_secret, encrypt_secret
from authentication.views import TWO_FACTOR_SETUP_KEY
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


class TwoFactorAuthenticationTests(TestCase):
    def setUp(self) -> None:
        self.user = FreyjaUser.objects.create_user(
            username="two-factor@example.com",
            email="two-factor@example.com",
            password="test-password",
        )

    def test_legacy_user_without_totp_is_sent_to_mandatory_setup(self) -> None:
        setup = self.client.post(
            reverse("api_auth_login"),
            {"email": self.user.email, "password": "test-password", "remember": False},
            content_type="application/json",
        )
        secret = self.client.session[TWO_FACTOR_SETUP_KEY]
        self.assertNotIn("_auth_user_id", self.client.session)

        invalid = self.client.post(
            reverse("api_auth_2fa_enable"), {"code": "000000"}, content_type="application/json"
        )
        valid = self.client.post(
            reverse("api_auth_2fa_enable"),
            {"code": code_at(secret)},
            content_type="application/json",
        )

        self.assertEqual(setup.status_code, 202)
        self.assertTrue(setup.json()["two_factor_setup_required"])
        self.assertTrue(setup.json()["qr_code"].startswith("data:image/png;base64,"))
        self.assertNotIn("secret", setup.json())
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.json()["user"]["id"], self.user.id)
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        self.assertNotEqual(self.user.totp_secret, secret)
        self.assertEqual(decrypt_secret(self.user.totp_secret), secret)

    def test_enabled_account_is_not_logged_in_until_totp_is_verified(self) -> None:
        secret = "JBSWY3DPEHPK3PXP"
        self.user.totp_secret = encrypt_secret(secret)
        self.user.two_factor_enabled = True
        self.user.save(update_fields=("totp_secret", "two_factor_enabled", "updated_at"))

        password_response = self.client.post(
            reverse("api_auth_login"),
            {"email": self.user.email, "password": "test-password", "remember": False},
            content_type="application/json",
        )
        anonymous_profile = self.client.get(reverse("api_auth_profile"))
        code_response = self.client.post(
            reverse("api_auth_login_2fa"),
            {"code": code_at(secret)},
            content_type="application/json",
        )

        self.assertEqual(password_response.status_code, 202)
        self.assertTrue(password_response.json()["two_factor_required"])
        self.assertEqual(anonymous_profile.status_code, 403)
        self.assertEqual(code_response.status_code, 200)
        self.assertEqual(code_response.json()["user"]["id"], self.user.id)

    def test_invalid_totp_does_not_complete_login(self) -> None:
        self.user.totp_secret = encrypt_secret("JBSWY3DPEHPK3PXP")
        self.user.two_factor_enabled = True
        self.user.save(update_fields=("totp_secret", "two_factor_enabled", "updated_at"))
        self.client.post(
            reverse("api_auth_login"),
            {"email": self.user.email, "password": "test-password"},
            content_type="application/json",
        )

        response = self.client.post(
            reverse("api_auth_login_2fa"), {"code": "000000"}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("authentication.views.verify_code", return_value=False)
    def test_challenge_is_cleared_after_five_invalid_codes(self, verify_code) -> None:
        self.user.totp_secret = encrypt_secret("JBSWY3DPEHPK3PXP")
        self.user.two_factor_enabled = True
        self.user.save(update_fields=("totp_secret", "two_factor_enabled", "updated_at"))
        self.client.post(
            reverse("api_auth_login"),
            {"email": self.user.email, "password": "test-password"},
            content_type="application/json",
        )

        for _ in range(5):
            response = self.client.post(
                reverse("api_auth_login_2fa"),
                {"code": "000000"},
                content_type="application/json",
            )

        self.assertEqual(response.json()["detail"], "Too many invalid codes. Sign in again.")
        self.assertNotIn("two_factor_login_challenge", self.client.session)

    def test_authenticated_session_without_totp_marker_cannot_bypass_2fa(self) -> None:
        self.user.totp_secret = encrypt_secret("JBSWY3DPEHPK3PXP")
        self.user.two_factor_enabled = True
        self.user.save(update_fields=("totp_secret", "two_factor_enabled", "updated_at"))
        self.client.force_login(self.user)

        response = self.client.get(reverse("api_auth_profile"))

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("authentication.views.Mailer")
    def test_registration_requires_totp_setup_before_login(self, mailer_class) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("api_auth_register"),
                {
                    "first_name": "New",
                    "last_name": "User",
                    "email": "new-user@example.com",
                    "password": "unique-secure-password-938!",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["two_factor_setup_required"])
        self.assertNotIn("_auth_user_id", self.client.session)


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
