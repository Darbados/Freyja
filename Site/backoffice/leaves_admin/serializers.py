from rest_framework import serializers

from authentication.serializers import UserSerializer
from leaves.models import Leave
from leaves.serializers import document_summary


class BackofficeLeaveSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()

    def get_document(self, leave):
        user = self.context["request"].user
        if user.has_perm("leaves.access_leave_documents") or user.pk in (
            leave.employee.user_id,
            leave.approver.user_id if leave.approver else None,
        ):
            return document_summary(leave.document) if hasattr(leave, "document") else None
        return None

    employee = UserSerializer(source="employee.user", read_only=True)
    approver = UserSerializer(source="approver.user", read_only=True, allow_null=True)
    reviewed_by = UserSerializer(read_only=True)
    duration_hours = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    duration_days = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    leave_type_label = serializers.CharField(source="get_leave_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Leave
        fields = (
            "id",
            "employee",
            "approver",
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
            "reviewed_at",
            "reviewed_by",
            "created_at",
            "updated_at",
            "document",
        )
