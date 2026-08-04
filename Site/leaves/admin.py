from django.contrib import admin

from leaves.models import Leave


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
    )
    list_filter = ("leave_type", "status")
    search_fields = (
        "employee__user__email",
        "employee__user__first_name",
        "employee__user__last_name",
        "comment",
    )
