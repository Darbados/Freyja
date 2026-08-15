from django.db import transaction
from rest_framework.exceptions import APIException, PermissionDenied

from backoffice.models import UserAdministrationEvent
from users.models import FreyjaUser


class UserAdministrationConflict(APIException):
    status_code = 409
    default_code = "user_administration_conflict"


class UserAdministrationService:
    """Applies security-sensitive user administration rules."""

    @staticmethod
    @transaction.atomic
    def deactivate(*, user: FreyjaUser, performed_by: FreyjaUser) -> FreyjaUser:
        user = FreyjaUser.objects.select_for_update().get(pk=user.pk)
        if not user.is_active:
            return user
        if user.pk == performed_by.pk:
            raise UserAdministrationConflict("You cannot deactivate your own account.")
        if user.is_superuser and not performed_by.is_superuser:
            raise PermissionDenied("Only a superuser can deactivate another superuser.")
        if user.is_superuser:
            active_superusers = FreyjaUser.objects.filter(
                is_active=True,
                is_superuser=True,
            ).count()
            if active_superusers == 1:
                raise UserAdministrationConflict("The last active superuser cannot be deactivated.")

        user.is_active = False
        user.save(update_fields=("is_active", "updated_at"))
        UserAdministrationEvent.objects.create(
            action=UserAdministrationEvent.Action.DEACTIVATED,
            target_user=user,
            target_email=user.email,
            performed_by=performed_by,
        )
        return user
