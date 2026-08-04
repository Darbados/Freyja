from django.urls import path

from leaves.views import LeaveRequestListCreateApiView


urlpatterns = [
    path("requests", LeaveRequestListCreateApiView.as_view(), name="leave_requests"),
]
