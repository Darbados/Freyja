from typing import Any

from django.test import Client

from authentication.middleware import TWO_FACTOR_VERIFIED_KEY


def force_two_factor_login(client: Client, user: Any) -> None:
    """Creates the fully verified session expected by authenticated feature tests."""
    user.two_factor_enabled = True
    user.totp_secret = "test-encrypted-secret"
    user.save(update_fields=("two_factor_enabled", "totp_secret", "updated_at"))
    client.force_login(user)
    session = client.session
    session[TWO_FACTOR_VERIFIED_KEY] = True
    session.save()
