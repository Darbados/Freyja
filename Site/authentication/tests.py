from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

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
