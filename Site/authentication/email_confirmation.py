from typing import Any

from django.conf import settings
from django.core import signing

from users.models import FreyjaUser


class EmailConfirmationSigner:
    """Creates and verifies expiring account-confirmation tokens."""

    salt = "authentication.email-confirmation"

    def create_token(self, user: FreyjaUser) -> str:
        return signing.dumps(
            {"user_id": user.pk, "email": user.email},
            salt=self.salt,
            compress=True,
        )

    def verify_token(self, token: str) -> FreyjaUser:
        payload: dict[str, Any] = signing.loads(
            token,
            salt=self.salt,
            max_age=settings.EMAIL_CONFIRMATION_TIMEOUT,
        )
        user = FreyjaUser.objects.filter(
            pk=payload.get("user_id"),
            email=payload.get("email"),
        ).first()
        if user is None:
            raise signing.BadSignature("The confirmation token does not match an account.")

        return user
