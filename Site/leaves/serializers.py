import datetime
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from authentication.serializers import UserSerializer
from leaves.models import Leave
from leaves.calendar import is_working_day


def document_summary(document) -> dict:
    return {
        "id": str(document.pk),
        "state": document.state,
        "label": document.get_state_display(),
        "template_version": document.template_version,
        "generated_at": document.generated_at,
        "sha256": document.sha256,
    }


class LeaveSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()
    client_request_id = serializers.UUIDField(required=False, write_only=True)
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
    can_cancel = serializers.BooleanField(read_only=True)

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
            "cancellation_reason",
            "canceled_at",
            "can_cancel",
            "approver",
            "created_at",
            "updated_at",
            "document",
            "client_request_id",
        )
        read_only_fields = ("status", "cancellation_reason", "canceled_at")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs.setdefault("leave_type", Leave.LeaveType.ANNUAL)
        attrs.setdefault("start_day_part", Leave.DayPart.FULL_DAY)
        attrs.setdefault("end_day_part", Leave.DayPart.FULL_DAY)
        attrs.setdefault("comment", "")
        start, end = attrs["start_date"], attrs["end_date"]
        if end - start > datetime.timedelta(days=366):
            raise serializers.ValidationError("A request may cover at most 367 calendar days.")
        if not is_working_day(start) or not is_working_day(end):
            raise serializers.ValidationError(
                "Leave must start and end on a Bulgarian working day."
            )
        if attrs["leave_type"] == Leave.LeaveType.ANNUAL and (
            attrs["start_day_part"] != Leave.DayPart.FULL_DAY
            or attrs["end_day_part"] != Leave.DayPart.FULL_DAY
        ):
            raise serializers.ValidationError("Bulgarian annual leave must use whole working days.")
        instance = Leave(**attrs)
        try:
            instance.clean()
        except DjangoValidationError as error:
            if hasattr(error, "message_dict"):
                raise serializers.ValidationError(error.message_dict) from error
            raise serializers.ValidationError(error.messages) from error
        return attrs

    def get_document(self, leave: Leave) -> dict | None:
        return document_summary(leave.document) if hasattr(leave, "document") else None

    def get_approver(self, leave: Leave) -> dict[str, Any] | None:
        if leave.approver is None:
            return None
        return UserSerializer(leave.approver.user).data


class LeaveCancellationSerializer(serializers.Serializer):
    reason = serializers.CharField(
        allow_blank=False,
        max_length=2000,
        trim_whitespace=True,
    )


class AnnualLeaveBalanceSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    entitlement_days = serializers.IntegerField()
    booked_days = serializers.DecimalField(max_digits=7, decimal_places=2)
    remaining_days = serializers.DecimalField(max_digits=7, decimal_places=2)


class TeamLeaveSerializer(LeaveSerializer):
    employee = UserSerializer(source="employee.user", read_only=True)

    class Meta(LeaveSerializer.Meta):
        fields = ("employee",) + LeaveSerializer.Meta.fields


class DepartmentLeaveSerializer(serializers.ModelSerializer):
    employee = UserSerializer(source="employee.user", read_only=True)
    duration_days = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Leave
        fields = (
            "id",
            "employee",
            "start_date",
            "end_date",
            "start_day_part",
            "end_day_part",
            "duration_days",
            "leave_type_label",
        )

    leave_type_label = serializers.CharField(source="get_leave_type_display", read_only=True)
