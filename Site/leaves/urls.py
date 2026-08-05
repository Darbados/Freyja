from django.urls import path

from leaves.views import LeaveRequestCancelApiView, LeaveRequestListCreateApiView


urlpatterns = [
    path("requests", LeaveRequestListCreateApiView.as_view(), name="leave_requests"),
    path(
        "requests/<int:leave_id>/cancel",
        LeaveRequestCancelApiView.as_view(),
        name="leave_request_cancel",
    ),
]
