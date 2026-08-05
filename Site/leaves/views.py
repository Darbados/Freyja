from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from employment.models import Employee
from leaves.balance import annual_leave_balance
from leaves.models import Leave
from leaves.serializers import (
    AnnualLeaveBalanceSerializer,
    LeaveCancellationSerializer,
    LeaveSerializer,
)


class LeaveRequestListCreateApiView(APIView):
    """Lists and creates leave requests for the signed-in employee."""

    def get(self, request: Request) -> Response:
        employee = get_object_or_404(Employee, user=request.user)
        leaves = employee.leave_requests.select_related("approver__user")
        balance = annual_leave_balance(employee, timezone.localdate().year)
        return Response(
            {
                "leave_requests": LeaveSerializer(leaves, many=True).data,
                "annual_leave_balance": AnnualLeaveBalanceSerializer(balance).data,
            }
        )

    def post(self, request: Request) -> Response:
        employee = get_object_or_404(
            Employee.objects.select_related(
                "user",
                "manager__user",
                "leave_approver__user",
            ),
            user=request.user,
        )
        approver = employee.leave_approver or employee.manager
        if approver is None:
            raise ValidationError(
                {"approver": "No manager or leave approver is assigned to your profile."}
            )

        serializer = LeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save(employee=employee, approver=approver)
        transaction.on_commit(lambda: self._notify_approver(leave))

        return Response(
            LeaveSerializer(leave).data,
            status=status.HTTP_201_CREATED,
        )

    def _notify_approver(self, leave: Leave) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        start = f"{leave.start_date:%d %b %Y} ({leave.get_start_day_part_display()})"
        end = f"{leave.end_date:%d %b %Y} ({leave.get_end_day_part_display()})"
        comment = leave.comment or "No comment provided."
        send_mail(
            subject=f"Leave request from {requester_name}",
            message=(
                f"{requester_name} submitted a leave request.\n\n"
                f"Period: {start} – {end}\n"
                f"Duration: {leave.duration_days} days\n"
                f"Type: {leave.get_leave_type_display()}\n"
                f"Comment: {comment}"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[leave.approver.user.email],
        )


class LeaveRequestCancelApiView(APIView):
    """Cancels one active leave request owned by the signed-in employee."""

    def post(self, request: Request, leave_id: int) -> Response:
        serializer = LeaveCancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            leave = get_object_or_404(
                Leave.objects.select_for_update().select_related(
                    "employee__user",
                    "approver__user",
                ),
                pk=leave_id,
                employee__user=request.user,
            )
            if leave.end_date < timezone.localdate():
                raise ValidationError(
                    {"detail": "A leave request cannot be canceled after its period has ended."}
                )
            if leave.status not in {Leave.Status.PENDING, Leave.Status.APPROVED}:
                raise ValidationError(
                    {"detail": "Only pending or approved leave requests can be canceled."}
                )

            leave.status = Leave.Status.CANCELED
            leave.cancellation_reason = serializer.validated_data["reason"]
            leave.canceled_at = timezone.now()
            leave.save(
                update_fields=(
                    "status",
                    "cancellation_reason",
                    "canceled_at",
                    "updated_at",
                )
            )
            if leave.approver is not None:
                transaction.on_commit(lambda: self._notify_approver(leave))

        return Response(LeaveSerializer(leave).data)

    def _notify_approver(self, leave: Leave) -> None:
        requester_name = leave.employee.user.get_full_name() or leave.employee.user.email
        send_mail(
            subject=f"Leave request canceled by {requester_name}",
            message=(
                f"{requester_name} canceled their leave request.\n\n"
                f"Period: {leave.start_date:%d %b %Y} – {leave.end_date:%d %b %Y}\n"
                f"Duration: {leave.duration_days} days\n"
                f"Cancellation reason: {leave.cancellation_reason}"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[leave.approver.user.email],
        )
