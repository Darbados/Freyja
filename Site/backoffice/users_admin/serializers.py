from rest_framework import serializers

from users.models import FreyjaUser


class BackofficeUserSerializer(serializers.ModelSerializer):
    """Represents account details safe for backoffice administrators."""

    class Meta:
        model = FreyjaUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "username",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "email_confirmed_at",
            "last_login",
            "created_at",
            "updated_at",
        )
