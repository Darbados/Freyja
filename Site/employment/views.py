from django.db.models import Count, Q
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from employment.models import Employee
from employment.serializers import OrganizationChartEmployeeSerializer


class OrganizationChartApiView(APIView):
    """Returns the active employee hierarchy as a flat, manager-linked list."""

    def get(self, request: Request) -> Response:
        employees = (
            Employee.objects.filter(user__is_active=True)
            .select_related("user", "manager__user")
            .annotate(
                direct_reports_count=Count(
                    "direct_reports",
                    filter=Q(direct_reports__user__is_active=True),
                )
            )
            .order_by("user__first_name", "user__last_name", "user__email")
        )
        serializer = OrganizationChartEmployeeSerializer(
            employees,
            many=True,
            context={"request": request},
        )
        return Response({"employees": serializer.data})
