from django.urls import path

from leaves.views import (
    DepartmentLeaveScheduleApiView,
    LeaveRequestCancelApiView,
    LeaveRequestListCreateApiView,
    TeamLeaveRequestListApiView,
)


urlpatterns = [
    path("requests", LeaveRequestListCreateApiView.as_view(), name="leave_requests"),
    path(
        "requests/<int:leave_id>/cancel",
        LeaveRequestCancelApiView.as_view(),
        name="leave_request_cancel",
    ),
    path(
        "team/requests",
        TeamLeaveRequestListApiView.as_view(),
        name="team_leave_requests",
    ),
    path(
        "department/schedule",
        DepartmentLeaveScheduleApiView.as_view(),
        name="department_leave_schedule",
    ),
]
