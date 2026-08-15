from django.urls import path

from backoffice.users_admin.api_views import (
    BackofficeUserDeactivateApiView,
    BackofficeUserDetailApiView,
    BackofficeUserListApiView,
    BackofficeUserSendConfirmationApiView,
)

urlpatterns = [
    path("users", BackofficeUserListApiView.as_view(), name="api_backoffice_users"),
    path(
        "users/<int:user_id>",
        BackofficeUserDetailApiView.as_view(),
        name="api_backoffice_user_detail",
    ),
    path(
        "users/<int:user_id>/deactivate",
        BackofficeUserDeactivateApiView.as_view(),
        name="api_backoffice_user_deactivate",
    ),
    path(
        "users/<int:user_id>/send-confirmation",
        BackofficeUserSendConfirmationApiView.as_view(),
        name="api_backoffice_user_send_confirmation",
    ),
]
