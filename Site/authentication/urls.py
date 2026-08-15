from django.urls import path

from authentication.views import (
    ConfirmEmailApiView,
    CsrfCookieView,
    HomeRedirectView,
    LoginApiView,
    LoginTwoFactorApiView,
    LoginPageView,
    LogoutPageView,
    LogoutApiView,
    PasswordResetApiView,
    PasswordResetCompletePageView,
    PasswordResetConfirmPageView,
    PasswordResetDonePageView,
    PasswordResetPageView,
    ProfileApiView,
    RegisterApiView,
    TwoFactorEnableApiView,
)

urlpatterns = [
    path("", HomeRedirectView.as_view(), name="auth_home"),
    path("login", LoginPageView.as_view(), name="login"),
    path("logout", LogoutPageView.as_view(), name="logout"),
    path("password-reset", PasswordResetPageView.as_view(), name="password_reset"),
    path("password-reset/done", PasswordResetDonePageView.as_view(), name="password_reset_done"),
    path(
        "reset/<uidb64>/<token>",
        PasswordResetConfirmPageView.as_view(),
        name="password_reset_confirm",
    ),
    path("reset/done", PasswordResetCompletePageView.as_view(), name="password_reset_complete"),
    path("api/auth/csrf", CsrfCookieView.as_view(), name="api_auth_csrf"),
    path("api/auth/login", LoginApiView.as_view(), name="api_auth_login"),
    path("api/auth/login/2fa", LoginTwoFactorApiView.as_view(), name="api_auth_login_2fa"),
    path("api/auth/2fa/enable", TwoFactorEnableApiView.as_view(), name="api_auth_2fa_enable"),
    path("api/auth/logout", LogoutApiView.as_view(), name="api_auth_logout"),
    path("api/auth/profile", ProfileApiView.as_view(), name="api_auth_profile"),
    path("api/auth/register", RegisterApiView.as_view(), name="api_auth_register"),
    path(
        "api/auth/email-confirmation/<str:token>",
        ConfirmEmailApiView.as_view(),
        name="api_auth_confirm_email",
    ),
    path("api/auth/password-reset", PasswordResetApiView.as_view(), name="api_auth_password_reset"),
]
