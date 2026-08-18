import datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Freyja.test_utils import force_two_factor_login
from backoffice.models import UserAdministrationEvent
from users.models import FreyjaUser


class UserListViewTests(TestCase):
    def setUp(self) -> None:
        self.staff_user = self._create_user("staff@example.com", is_staff=True)

    def test_requires_a_staff_user(self) -> None:
        response = self.client.get(reverse("backoffice:users_list"))
        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('backoffice:users_list')}",
        )

        force_two_factor_login(self.client, self._create_user("employee@example.com"))
        response = self.client.get(reverse("backoffice:users_list"))
        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('backoffice:users_list')}",
        )

    def test_displays_requested_user_fields(self) -> None:
        confirmed_at = timezone.now()
        user = self._create_user("confirmed@example.com")
        user.email_confirmed_at = confirmed_at
        user.save(update_fields=("email_confirmed_at", "updated_at"))
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("backoffice:users_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.email)
        self.assertContains(response, user.date_joined.strftime("%b %-d, %Y, %H:%M"))
        self.assertContains(response, confirmed_at.strftime("%b %-d, %Y, %H:%M"))

    def test_paginates_users_fifty_per_page(self) -> None:
        FreyjaUser.objects.bulk_create(
            FreyjaUser(
                username=f"user-{number}@example.com",
                email=f"user-{number}@example.com",
                date_joined=timezone.now() + datetime.timedelta(seconds=number),
            )
            for number in range(51)
        )
        force_two_factor_login(self.client, self.staff_user)

        first_page = self.client.get(reverse("backoffice:users_list"))
        second_page = self.client.get(reverse("backoffice:users_list"), {"page": 2})

        self.assertEqual(len(first_page.context["users"]), 50)
        self.assertEqual(first_page.context["paginator"].per_page, 50)
        self.assertEqual(len(second_page.context["users"]), 2)

    def test_links_each_user_to_their_details(self) -> None:
        user = self._create_user("details@example.com")
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("backoffice:users_list"))

        self.assertContains(
            response,
            reverse("backoffice:user_detail", args=(user.pk,)),
        )

    @staticmethod
    def _create_user(email: str, *, is_staff: bool = False) -> FreyjaUser:
        return FreyjaUser.objects.create_user(
            username=email,
            email=email,
            password="test-password",
            is_staff=is_staff,
        )


class UserDetailViewTests(TestCase):
    def setUp(self) -> None:
        self.staff_user = UserListViewTests._create_user(
            "staff-details@example.com",
            is_staff=True,
        )
        self.user = UserListViewTests._create_user("user-details@example.com")
        self.user.first_name = "Emma"
        self.user.last_name = "Employee"
        self.user.email_confirmed_at = timezone.now()
        self.user.last_login = timezone.now()
        self.user.save(
            update_fields=(
                "first_name",
                "last_name",
                "email_confirmed_at",
                "last_login",
                "updated_at",
            )
        )

    def test_requires_a_staff_user(self) -> None:
        url = reverse("backoffice:user_detail", args=(self.user.pk,))

        response = self.client.get(url)

        self.assertRedirects(response, f"{reverse('admin:login')}?next={url}")

    def test_displays_user_account_details(self) -> None:
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("backoffice:user_detail", args=(self.user.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Emma Employee")
        self.assertContains(response, self.user.email)
        self.assertContains(response, "Email confirmed")
        self.assertContains(response, self.user.date_joined.strftime("%b %-d, %Y, %H:%M"))
        self.assertContains(response, self.user.last_login.strftime("%b %-d, %Y, %H:%M"))

    def test_returns_not_found_for_an_unknown_user(self) -> None:
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("backoffice:user_detail", args=(999999,)))

        self.assertEqual(response.status_code, 404)


class BackofficeUserApiTests(TestCase):
    def setUp(self) -> None:
        self.staff_user = UserListViewTests._create_user(
            "api-staff@example.com",
            is_staff=True,
        )
        self.user = UserListViewTests._create_user("api-user@example.com")

    def test_requires_a_staff_user(self) -> None:
        detail_url = reverse("api_backoffice_user_detail", args=(self.user.pk,))

        anonymous_response = self.client.get(detail_url)
        force_two_factor_login(self.client, self.user)
        user_response = self.client.get(detail_url)

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(user_response.status_code, 403)

    def test_lists_fifty_users_per_page(self) -> None:
        FreyjaUser.objects.bulk_create(
            FreyjaUser(
                username=f"api-user-{number}@example.com",
                email=f"api-user-{number}@example.com",
                date_joined=timezone.now() + datetime.timedelta(seconds=number),
            )
            for number in range(50)
        )
        force_two_factor_login(self.client, self.staff_user)

        first_page = self.client.get(reverse("api_backoffice_users"))
        second_page = self.client.get(reverse("api_backoffice_users"), {"page": 2})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.json()["count"], 52)
        self.assertEqual(len(first_page.json()["results"]), 50)
        self.assertEqual(len(second_page.json()["results"]), 2)

    def test_returns_user_details(self) -> None:
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.get(reverse("api_backoffice_user_detail", args=(self.user.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], self.user.email)
        self.assertTrue(response.json()["is_active"])

    def test_deactivates_and_audits_a_user(self) -> None:
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.post(
            reverse("api_backoffice_user_deactivate", args=(self.user.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        event = UserAdministrationEvent.objects.get(
            action=UserAdministrationEvent.Action.DEACTIVATED
        )
        self.assertEqual(event.target_user, self.user)
        self.assertEqual(event.target_email, self.user.email)
        self.assertEqual(event.performed_by, self.staff_user)

    def test_deactivation_is_idempotent(self) -> None:
        self.user.is_active = False
        self.user.save(update_fields=("is_active", "updated_at"))
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.post(
            reverse("api_backoffice_user_deactivate", args=(self.user.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])
        self.assertFalse(UserAdministrationEvent.objects.exists())

    def test_cannot_deactivate_own_account(self) -> None:
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.post(
            reverse("api_backoffice_user_deactivate", args=(self.staff_user.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.staff_user.refresh_from_db()
        self.assertTrue(self.staff_user.is_active)

    def test_staff_user_cannot_deactivate_a_superuser(self) -> None:
        superuser = FreyjaUser.objects.create_superuser(
            username="superuser@example.com",
            email="superuser@example.com",
            password="test-password",
        )
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.post(
            reverse("api_backoffice_user_deactivate", args=(superuser.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        superuser.refresh_from_db()
        self.assertTrue(superuser.is_active)

    def test_last_active_superuser_cannot_be_deactivated(self) -> None:
        superuser = FreyjaUser.objects.create_superuser(
            username="last-superuser@example.com",
            email="last-superuser@example.com",
            password="test-password",
        )
        force_two_factor_login(self.client, superuser)

        response = self.client.post(
            reverse("api_backoffice_user_deactivate", args=(self.staff_user.pk,)),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        other_superuser = FreyjaUser.objects.create_superuser(
            username="other-superuser@example.com",
            email="other-superuser@example.com",
            password="test-password",
        )
        other_superuser.is_active = False
        other_superuser.save(update_fields=("is_active", "updated_at"))

        response = self.client.post(
            reverse("api_backoffice_user_deactivate", args=(superuser.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        superuser.refresh_from_db()
        self.assertTrue(superuser.is_active)

    @patch("backoffice.users_admin.api_views.Mailer")
    def test_sends_and_audits_confirmation_email(self, mailer_class) -> None:
        force_two_factor_login(self.client, self.staff_user)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("api_backoffice_user_send_confirmation", args=(self.user.pk,)),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        call = mailer_class.return_value.send_account_confirmation.call_args
        self.assertEqual(call.args[0], self.user)
        self.assertIn("/api/auth/email-confirmation/", call.args[1])
        event = UserAdministrationEvent.objects.get(
            action=UserAdministrationEvent.Action.CONFIRMATION_SENT
        )
        self.assertEqual(event.target_user, self.user)
        self.assertEqual(event.performed_by, self.staff_user)

    @patch("backoffice.users_admin.api_views.Mailer")
    def test_does_not_send_confirmation_to_confirmed_user(self, mailer_class) -> None:
        self.user.email_confirmed_at = timezone.now()
        self.user.save(update_fields=("email_confirmed_at", "updated_at"))
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.post(
            reverse("api_backoffice_user_send_confirmation", args=(self.user.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        mailer_class.return_value.send_account_confirmation.assert_not_called()
        self.assertFalse(UserAdministrationEvent.objects.exists())

    @patch("backoffice.users_admin.api_views.Mailer")
    def test_does_not_send_confirmation_to_inactive_user(self, mailer_class) -> None:
        self.user.is_active = False
        self.user.save(update_fields=("is_active", "updated_at"))
        force_two_factor_login(self.client, self.staff_user)

        response = self.client.post(
            reverse("api_backoffice_user_send_confirmation", args=(self.user.pk,)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        mailer_class.return_value.send_account_confirmation.assert_not_called()
