from django.urls import path

from employment.views import OrganizationChartApiView, OrganizationChartExportApiView


urlpatterns = [
    path("organization-chart", OrganizationChartApiView.as_view(), name="organization_chart"),
    path(
        "organization-chart/export",
        OrganizationChartExportApiView.as_view(),
        name="organization_chart_export",
    ),
    path(
        "organization-chart/<int:employee_id>/export",
        OrganizationChartExportApiView.as_view(),
        name="organization_chart_subtree_export",
    ),
]
