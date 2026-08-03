from rest_framework import serializers

from employment.models import Employee


class OrganizationChartEmployeeSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    avatar = serializers.SerializerMethodField()
    manager_id = serializers.SerializerMethodField()
    direct_reports_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Employee
        fields = (
            "id",
            "user_id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "job_title",
            "manager_id",
            "direct_reports_count",
        )

    def get_avatar(self, employee: Employee) -> str | None:
        if not employee.user.avatar:
            return None

        request = self.context.get("request")
        return (
            request.build_absolute_uri(employee.user.avatar.url)
            if request
            else employee.user.avatar.url
        )

    def get_manager_id(self, employee: Employee) -> int | None:
        if employee.manager is None or not employee.manager.user.is_active:
            return None
        return employee.manager_id
