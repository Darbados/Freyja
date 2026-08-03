import csv
from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook

from employment.models import Employee


SpreadsheetRow = tuple[int | str, ...]


class OrganizationChartSpreadsheetGenerator:
    """Generates downloadable organization-chart spreadsheets."""

    def __init__(self, employees: list[Employee]) -> None:
        self.employees = employees
        employee_ids = {employee.id for employee in employees}
        self.children_by_manager: dict[int | None, list[Employee]] = {}

        for employee in employees:
            manager_id = employee.manager_id
            if manager_id not in employee_ids:
                manager_id = None
            self.children_by_manager.setdefault(manager_id, []).append(employee)

    def generate(self, export_format: str, root: Employee | None = None) -> HttpResponse:
        roots = [root] if root else self.children_by_manager.get(None, [])
        rows = self._subtree_rows(roots)
        filename_base = (
            f"freyja-{self._filename_name(root)}-team"
            if root
            else "freyja-organization-chart"
        )

        if export_format == "xlsx":
            return self._xlsx_response(rows, filename_base)
        return self._csv_response(rows, filename_base)

    def _csv_response(self, rows: list[SpreadsheetRow], filename_base: str) -> HttpResponse:
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename_base}.csv"'
        response.write("\ufeff")
        csv.writer(response).writerows(rows)
        return response

    def _xlsx_response(self, rows: list[SpreadsheetRow], filename_base: str) -> HttpResponse:
        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet("Organization chart")
        for row in rows:
            worksheet.append(row)

        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename_base}.xlsx"'
        return response

    def _subtree_rows(self, roots: list[Employee]) -> list[SpreadsheetRow]:
        rows: list[SpreadsheetRow] = [
            ("Level", "Employee", "Job title", "Email", "Manager")
        ]
        stack = [(root, 0, "") for root in reversed(roots)]
        while stack:
            employee, level, manager_name = stack.pop()
            employee_name = employee.user.get_full_name() or employee.user.email
            rows.append(
                (
                    level,
                    employee_name,
                    employee.job_title,
                    employee.user.email,
                    manager_name,
                )
            )
            children = self.children_by_manager.get(employee.id, [])
            stack.extend(
                (child, level + 1, employee_name) for child in reversed(children)
            )
        return rows

    def _filename_name(self, employee: Employee) -> str:
        name = employee.user.get_full_name() or employee.user.email.split("@", 1)[0]
        safe_name = "-".join(name.lower().split())
        filename_name = "".join(
            character for character in safe_name if character.isalnum() or character == "-"
        )
        return filename_name or f"employee-{employee.pk}"
