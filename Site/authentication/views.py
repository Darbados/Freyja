from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core import signing
from django.db import transaction
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.urls import reverse
from django.views.generic import RedirectView
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from Freyja.mailer import Mailer
from authentication.forms import EmailAuthenticationForm, EmailPasswordResetForm
from authentication.middleware import TWO_FACTOR_VERIFIED_KEY
from authentication.email_confirmation import EmailConfirmationSigner
from authentication.serializers import (
    LoginSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
    TotpCodeSerializer,
)
from authentication.totp import (
    decrypt_secret,
    encrypt_secret,
    generate_secret,
    qr_code_data_url,
    verify_code,
)

TWO_FACTOR_CHALLENGE_KEY = "two_factor_login_challenge"
TWO_FACTOR_SETUP_KEY = "two_factor_setup_secret"
TWO_FACTOR_MAX_ATTEMPTS = 5


def _reject_challenge_attempt(request: Request, detail: str) -> Response:
    challenge = request.session.get(TWO_FACTOR_CHALLENGE_KEY)
    if challenge is not None:
        challenge["attempts"] = challenge.get("attempts", 0) + 1
        request.session[TWO_FACTOR_CHALLENGE_KEY] = challenge
        if challenge["attempts"] >= TWO_FACTOR_MAX_ATTEMPTS:
            request.session.pop(TWO_FACTOR_CHALLENGE_KEY, None)
            request.session.pop(TWO_FACTOR_SETUP_KEY, None)
            detail = "Too many invalid codes. Sign in again."
    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfCookieView(APIView):
    """Represents a CSRF bootstrap endpoint for session auth."""

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user_data: dict[str, Any] | None = None
        if request.user.is_authenticated:
            user_data = UserSerializer(request.user).data

        return Response({"authenticated": request.user.is_authenticated, "user": user_data})


class LoginApiView(APIView):
    """Represents a session login endpoint."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        remember = serializer.validated_data["remember"]

        user = authenticate(request=request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        challenge = {
            "user_id": user.pk,
            "remember": remember,
            "created_at": timezone.now().timestamp(),
            "attempts": 0,
        }
        request.session[TWO_FACTOR_CHALLENGE_KEY] = challenge
        request.session.pop(TWO_FACTOR_SETUP_KEY, None)
        if not user.two_factor_enabled:
            secret = generate_secret()
            request.session[TWO_FACTOR_SETUP_KEY] = secret
            return Response(
                {
                    "two_factor_setup_required": True,
                    "qr_code": qr_code_data_url(secret, user.email),
                    "secret": secret,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        return Response({"two_factor_required": True}, status=status.HTTP_202_ACCEPTED)


class LoginTwoFactorApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = TotpCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        challenge = request.session.get(TWO_FACTOR_CHALLENGE_KEY)
        if not challenge or timezone.now().timestamp() - challenge["created_at"] > 300:
            request.session.pop(TWO_FACTOR_CHALLENGE_KEY, None)
            request.session.pop(TWO_FACTOR_SETUP_KEY, None)
            return Response(
                {"detail": "Your two-factor login expired. Sign in again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from users.models import FreyjaUser

        user = FreyjaUser.objects.filter(pk=challenge["user_id"], is_active=True).first()
        if (
            user is None
            or not user.two_factor_enabled
            or not verify_code(decrypt_secret(user.totp_secret), serializer.validated_data["code"])
        ):
            return _reject_challenge_attempt(request, "Invalid authentication code.")

        remember = challenge["remember"]
        request.session.pop(TWO_FACTOR_CHALLENGE_KEY, None)
        login(request, user)
        request.session[TWO_FACTOR_VERIFIED_KEY] = True
        request.session.set_expiry(settings.SESSION_COOKIE_AGE if remember else 0)
        return Response({"user": UserSerializer(user).data})


class TwoFactorEnableApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = TotpCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        secret = request.session.get(TWO_FACTOR_SETUP_KEY)
        challenge = request.session.get(TWO_FACTOR_CHALLENGE_KEY)
        if (
            secret is None
            or challenge is None
            or timezone.now().timestamp() - challenge["created_at"] > 300
            or not verify_code(secret, serializer.validated_data["code"])
        ):
            return _reject_challenge_attempt(request, "Invalid authentication code.")
        from users.models import FreyjaUser

        user = FreyjaUser.objects.filter(pk=challenge["user_id"], is_active=True).first()
        if user is None:
            return Response({"detail": "Invalid two-factor setup."}, status=400)
        user.totp_secret = encrypt_secret(secret)
        user.two_factor_enabled = True
        user.save(update_fields=("totp_secret", "two_factor_enabled", "updated_at"))
        login(request, user)
        request.session[TWO_FACTOR_VERIFIED_KEY] = True
        request.session.set_expiry(settings.SESSION_COOKIE_AGE if challenge["remember"] else 0)
        request.session.pop(TWO_FACTOR_SETUP_KEY, None)
        request.session.pop(TWO_FACTOR_CHALLENGE_KEY, None)
        return Response({"user": UserSerializer(user).data})


class LogoutApiView(APIView):
    """Ends the current authenticated session."""

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileApiView(APIView):
    """Reads and updates the current user's client-facing profile."""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(ProfileSerializer(request.user, context={"request": request}).data)

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RegisterApiView(APIView):
    """Represents a registration endpoint."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = EmailConfirmationSigner().create_token(user)
        confirmation_url = request.build_absolute_uri(
            reverse("api_auth_confirm_email", args=(token,))
        )
        transaction.on_commit(lambda: Mailer().send_account_confirmation(user, confirmation_url))
        secret = generate_secret()
        request.session[TWO_FACTOR_CHALLENGE_KEY] = {
            "user_id": user.pk,
            "remember": True,
            "created_at": timezone.now().timestamp(),
            "attempts": 0,
        }
        request.session[TWO_FACTOR_SETUP_KEY] = secret

        return Response(
            {
                "organization": getattr(user, "_pending_organization_name", ""),
                "two_factor_setup_required": True,
                "qr_code": qr_code_data_url(secret, user.email),
                "secret": secret,
            },
            status=status.HTTP_201_CREATED,
        )


class ConfirmEmailApiView(APIView):
    """Confirms a user's email address from an expiring signed link."""

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, token: str, *args: Any, **kwargs: Any) -> Response:
        try:
            user = EmailConfirmationSigner().verify_token(token)
        except signing.BadSignature:
            return Response(
                {"detail": "This confirmation link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.email_confirmed_at is None:
            user.email_confirmed_at = timezone.now()
            user.save(update_fields=("email_confirmed_at", "updated_at"))

        return Response({"detail": "Your email address has been confirmed."})


class PasswordResetApiView(APIView):
    """Represents a password reset request endpoint."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = EmailPasswordResetForm(data=serializer.validated_data)
        if form.is_valid():
            form.save(
                request=request._request,
                use_https=request.is_secure(),
                from_email=None,
            )

        return Response(
            {
                "detail": (
                    "If an account with that email exists, password reset instructions have been sent."
                )
            }
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginPageView(LoginView):
    """Represents the Django login page."""

    authentication_form = EmailAuthenticationForm
    template_name = "authentication/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        return settings.LOGIN_REDIRECT_URL


class HomeRedirectView(RedirectView):
    """Represents a redirect from the root URL to the login page."""

    pattern_name = "login"
    permanent = False


class LogoutPageView(LogoutView):
    """Represents the Django logout page."""


class PasswordResetPageView(PasswordResetView):
    """Represents the Django password reset request page."""

    form_class = EmailPasswordResetForm
    template_name = "registration/password_reset_form.html"


class PasswordResetDonePageView(PasswordResetDoneView):
    """Represents the Django password reset sent page."""

    template_name = "registration/password_reset_done.html"


class PasswordResetConfirmPageView(PasswordResetConfirmView):
    """Represents the Django password reset confirmation page."""

    template_name = "registration/password_reset_confirm.html"


class PasswordResetCompletePageView(PasswordResetCompleteView):
    """Represents the Django password reset complete page."""

    template_name = "registration/password_reset_complete.html"
