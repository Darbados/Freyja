from collections.abc import Callable

from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse


TWO_FACTOR_VERIFIED_KEY = "two_factor_verified"


class RequireTwoFactorMiddleware:
    """Rejects authenticated sessions that bypassed TOTP verification."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated and (
            not request.user.two_factor_enabled or not request.session.get(TWO_FACTOR_VERIFIED_KEY)
        ):
            logout(request)
        return self.get_response(request)
