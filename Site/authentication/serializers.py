from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from employment.models import Employee, Employment, EmploymentType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Represents a serialized Freyja user."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "email_confirmed_at",
            "is_staff",
            "is_superuser",
            "two_factor_enabled",
        )


class EmploymentTypeSerializer(serializers.ModelSerializer):
    """Represents the employment type details shown on an employee profile."""

    class Meta:
        model = EmploymentType
        fields = (
            "id",
            "name",
            "code",
            "relationship_kind",
            "paid_leave_eligible",
            "default_base_leave_days",
            "is_active",
        )


class EmploymentSerializer(serializers.ModelSerializer):
    """Represents one employment record shown on an employee profile."""

    employment_type = EmploymentTypeSerializer(read_only=True)
    base_leave_days = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Employment
        fields = (
            "id",
            "employment_type",
            "start_date",
            "end_date",
            "base_leave_days_override",
            "base_leave_days",
            "created_at",
            "updated_at",
        )


class ProfileSerializer(serializers.ModelSerializer):
    """Represents the safe, client-facing profile for the current user."""

    avatar = serializers.SerializerMethodField()
    manager = serializers.SerializerMethodField()
    departments = serializers.SerializerMethodField()
    employments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "manager",
            "departments",
            "employments",
            "is_active",
            "email_confirmed_at",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
            "two_factor_enabled",
        )
        read_only_fields = (
            "id",
            "email",
            "avatar",
            "manager",
            "departments",
            "employments",
            "is_active",
            "email_confirmed_at",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
            "two_factor_enabled",
        )

    def get_avatar(self, user: Any) -> str | None:
        if not user.avatar:
            return None

        request = self.context.get("request")
        return request.build_absolute_uri(user.avatar.url) if request else user.avatar.url

    def get_manager(self, user: Any) -> dict[str, Any] | None:
        employee = Employee.objects.select_related("manager__user").filter(user=user).first()
        if employee is None or employee.manager is None:
            return None

        manager = employee.manager.user
        return {
            "id": manager.id,
            "email": manager.email,
            "first_name": manager.first_name,
            "last_name": manager.last_name,
        }

    def get_departments(self, user: Any) -> list[dict[str, Any]]:
        departments = {
            assignment.department_id: assignment.department.name
            for assignment in user.department_assignments.select_related("department")
        }
        departments.update(
            {department.id: department.name for department in user.departments.all()}
        )
        return [
            {"id": department_id, "name": name}
            for department_id, name in sorted(departments.items(), key=lambda item: item[1].lower())
        ]

    def get_employments(self, user: Any) -> list[dict[str, Any]]:
        employee = (
            Employee.objects.prefetch_related("employments__employment_type")
            .filter(user=user)
            .first()
        )
        if employee is None:
            return []

        return EmploymentSerializer(employee.employments.all(), many=True).data


class LoginSerializer(serializers.Serializer):
    """Represents a login request payload."""

    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)
    remember = serializers.BooleanField(default=False)


class TotpCodeSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^\d{6}$", trim_whitespace=True)


class RegisterSerializer(serializers.Serializer):
    """Represents a registration request payload."""

    first_name = serializers.CharField(default="")
    last_name = serializers.CharField(default="")
    email = serializers.EmailField()
    organization = serializers.CharField(default="")
    password = serializers.CharField(trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return value

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict[str, Any]) -> Any:
        organization = validated_data.pop("organization", "")
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
        )
        Employee.objects.create(user=user)
        user._pending_organization_name = organization
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Represents a password reset request payload."""

    email = serializers.EmailField()
