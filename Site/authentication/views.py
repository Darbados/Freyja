from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.utils.decorators import method_decorator
from django.views.generic import RedirectView
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.forms import EmailAuthenticationForm, EmailPasswordResetForm
from authentication.serializers import (
    LoginSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)


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

        login(request, user)
        if not remember:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)

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
        login(request, user)
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)

        return Response(
            {
                "user": UserSerializer(user).data,
                "organization": getattr(user, "_pending_organization_name", ""),
            },
            status=status.HTTP_201_CREATED,
        )


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
                email_template_name="registration/password_reset_email.txt",
                subject_template_name="registration/password_reset_subject.txt",
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
    email_template_name = "registration/password_reset_email.txt"
    subject_template_name = "registration/password_reset_subject.txt"


class PasswordResetDonePageView(PasswordResetDoneView):
    """Represents the Django password reset sent page."""

    template_name = "registration/password_reset_done.html"


class PasswordResetConfirmPageView(PasswordResetConfirmView):
    """Represents the Django password reset confirmation page."""

    template_name = "registration/password_reset_confirm.html"


class PasswordResetCompletePageView(PasswordResetCompleteView):
    """Represents the Django password reset complete page."""

    template_name = "registration/password_reset_complete.html"
