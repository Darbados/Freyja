from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from authentication.serializers import UserSerializer
from leaves.models import Leave


class LeaveSerializer(serializers.ModelSerializer):
    duration_hours = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    duration_days = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    leave_type_label = serializers.CharField(source="get_leave_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    approver = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = (
            "id",
            "start_date",
            "end_date",
            "start_day_part",
            "end_day_part",
            "duration_hours",
            "duration_days",
            "leave_type",
            "leave_type_label",
            "status",
            "status_label",
            "comment",
            "approver",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status",)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance = Leave(**attrs)
        try:
            instance.clean()
        except DjangoValidationError as error:
            if hasattr(error, "message_dict"):
                raise serializers.ValidationError(error.message_dict) from error
            raise serializers.ValidationError(error.messages) from error
        return attrs

    def get_approver(self, leave: Leave) -> dict[str, Any] | None:
        if leave.approver is None:
            return None
        return UserSerializer(leave.approver.user).data
