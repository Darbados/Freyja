from django.contrib import admin

from employment.models import Employee, Employment, EmploymentType


@admin.register(EmploymentType)
class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "relationship_kind",
        "paid_leave_eligible",
        "default_base_leave_days",
        "is_active",
    )
    list_filter = ("relationship_kind", "paid_leave_eligible", "is_active")
    search_fields = ("name", "code")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "job_title", "manager", "created_at", "updated_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "job_title")


@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ("employee", "employment_type", "start_date", "end_date", "base_leave_days")
    list_filter = ("employment_type",)
    search_fields = (
        "employee__user__email",
        "employee__user__first_name",
        "employee__user__last_name",
    )
