from django.urls import path

from employment.views import OrganizationChartApiView


urlpatterns = [
    path("organization-chart", OrganizationChartApiView.as_view(), name="organization_chart"),
]
