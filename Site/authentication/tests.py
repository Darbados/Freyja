from unittest.mock import patch

from django.test import SimpleTestCase

from authentication.forms import EmailPasswordResetForm


class EmailPasswordResetFormTests(SimpleTestCase):
    @patch("authentication.forms.Mailer")
    def test_delegates_email_delivery_to_mailer(self, mailer_class) -> None:
        context = {"domain": "example.com"}

        EmailPasswordResetForm().send_mail(
            "registration/password_reset_subject.txt",
            "registration/password_reset_email.txt",
            context,
            "from@example.com",
            "employee@example.com",
        )

        mailer_class.return_value.send_forgotten_password.assert_called_once_with(
            subject_template_name="registration/password_reset_subject.txt",
            email_template_name="registration/password_reset_email.txt",
            context=context,
            recipient="employee@example.com",
            from_email="from@example.com",
            html_email_template_name=None,
        )
