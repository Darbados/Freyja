from django.urls import path

from leaves.views import (
    DepartmentLeaveScheduleApiView,
    LeaveRequestCancelApiView,
    LeaveRequestListCreateApiView,
    TeamLeaveRequestListApiView,
    LeaveDocumentApiView,
    LeaveDocumentPdfApiView,
    LeaveDocumentRetryApiView,
    LeaveEstimateApiView,
)


urlpatterns = [
    path("estimate", LeaveEstimateApiView.as_view(), name="leave_estimate"),
    path("requests/<int:leave_id>/document", LeaveDocumentApiView.as_view(), name="leave_document"),
    path(
        "requests/<int:leave_id>/document/pdf",
        LeaveDocumentPdfApiView.as_view(),
        name="leave_document_pdf",
    ),
    path(
        "requests/<int:leave_id>/document/retry",
        LeaveDocumentRetryApiView.as_view(),
        name="leave_document_retry",
    ),
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
