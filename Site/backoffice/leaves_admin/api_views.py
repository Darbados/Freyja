from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backoffice.leaves_admin.serializers import BackofficeLeaveSerializer
from leaves.models import Leave


class BackofficeLeavePagination(PageNumberPagination):
    page_size = 50


class BackofficeLeaveListApiView(APIView):
    """Lists all leave requests for backoffice staff."""

    permission_classes = (IsAdminUser,)

    def get(self, request: Request) -> Response:
        leaves = Leave.objects.select_related(
            "employee__user",
            "approver__user",
            "reviewed_by",
        ).order_by("-created_at", "-pk")
        paginator = BackofficeLeavePagination()
        page = paginator.paginate_queryset(leaves, request, view=self)
        serializer = BackofficeLeaveSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class BackofficeLeaveDetailApiView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request: Request, leave_id: int) -> Response:
        leave = get_object_or_404(
            Leave.objects.select_related("employee__user", "approver__user", "reviewed_by"),
            pk=leave_id,
        )
        return Response(BackofficeLeaveSerializer(leave).data)
