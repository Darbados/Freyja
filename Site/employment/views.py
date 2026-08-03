from django.db.models import Count, Q

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from employment.models import Employee
from employment.serializers import OrganizationChartEmployeeSerializer
from employment.spreadsheet_generation import OrganizationChartSpreadsheetGenerator


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


class OrganizationChartExportApiView(APIView):
    """Exports the active organization or one manager's subtree as CSV or XLSX."""

    def get(self, request: Request, employee_id: int | None = None) -> HttpResponse:
        export_format = request.query_params.get("file_format", "csv").lower()
        if export_format not in {"csv", "xlsx"}:
            raise ValidationError({"file_format": "Choose either 'csv' or 'xlsx'."})

        employees = list(
            Employee.objects.filter(user__is_active=True)
            .select_related("user", "manager__user")
            .order_by("user__first_name", "user__last_name", "user__email")
        )
        root = None
        if employee_id is not None:
            root = get_object_or_404(
                Employee.objects.select_related("user"),
                pk=employee_id,
                user__is_active=True,
            )

        return OrganizationChartSpreadsheetGenerator(employees).generate(
            export_format,
            root,
        )
