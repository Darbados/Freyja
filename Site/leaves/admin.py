from django.contrib import admin

from leaves.models import Leave, LeaveDocument


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "start_date",
        "end_date",
        "duration_hours",
        "leave_type",
        "status",
        "approver",
        "canceled_at",
    )
    list_filter = ("leave_type", "status")
    search_fields = (
        "employee__user__email",
        "employee__user__first_name",
        "employee__user__last_name",
        "comment",
        "cancellation_reason",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and hasattr(obj, "document"):
            return (
                "employee",
                "start_date",
                "end_date",
                "start_day_part",
                "end_day_part",
                "leave_type",
            )
        return ()


@admin.register(LeaveDocument)
class LeaveDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "leave", "state", "generated_at", "attempts")
    exclude = ("pdf",)

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields if field.name != "pdf")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("leaves.access_leave_documents")
