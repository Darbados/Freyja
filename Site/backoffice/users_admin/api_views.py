from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from Freyja.mailer import Mailer
from authentication.email_confirmation import EmailConfirmationSigner
from backoffice.models import UserAdministrationEvent
from backoffice.users_admin.serializers import BackofficeUserSerializer
from backoffice.users_admin.services import UserAdministrationService
from users.models import FreyjaUser


class BackofficeUserPagination(PageNumberPagination):
    page_size = 50


class BackofficeUserListApiView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request: Request) -> Response:
        users = FreyjaUser.objects.order_by("-date_joined", "-pk")
        paginator = BackofficeUserPagination()
        page = paginator.paginate_queryset(users, request, view=self)
        serializer = BackofficeUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class BackofficeUserDetailApiView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request: Request, user_id: int) -> Response:
        user = get_object_or_404(FreyjaUser, pk=user_id)
        return Response(BackofficeUserSerializer(user).data)


class BackofficeUserDeactivateApiView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request: Request, user_id: int) -> Response:
        user = get_object_or_404(FreyjaUser, pk=user_id)
        user = UserAdministrationService.deactivate(user=user, performed_by=request.user)
        return Response(BackofficeUserSerializer(user).data)


class ConfirmationEmailConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "confirmation_email_conflict"


class BackofficeUserSendConfirmationApiView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request: Request, user_id: int) -> Response:
        user = get_object_or_404(FreyjaUser, pk=user_id)
        if not user.is_active:
            raise ConfirmationEmailConflict(
                "A confirmation email cannot be sent to an inactive user."
            )
        if user.email_confirmed_at is not None:
            raise ConfirmationEmailConflict("This user's email address is already confirmed.")

        token = EmailConfirmationSigner().create_token(user)
        confirmation_url = request.build_absolute_uri(
            reverse("api_auth_confirm_email", args=(token,))
        )

        def send_confirmation() -> None:
            Mailer().send_account_confirmation(user, confirmation_url)

        with transaction.atomic():
            UserAdministrationEvent.objects.create(
                action=UserAdministrationEvent.Action.CONFIRMATION_SENT,
                target_user=user,
                target_email=user.email,
                performed_by=request.user,
            )
            transaction.on_commit(send_confirmation)

        return Response(
            {"detail": f"A confirmation email was sent to {user.email}."},
            status=status.HTTP_200_OK,
        )
