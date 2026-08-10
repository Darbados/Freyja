from django.urls import path
from django.views.generic import RedirectView

from backoffice.users_admin.views import UserDetailView, UserListView

app_name = "backoffice"

urlpatterns = [
    path(
        "backoffice",
        RedirectView.as_view(pattern_name="backoffice:users_list", permanent=False),
        name="index",
    ),
    path("backoffice/users", UserListView.as_view(), name="users_list"),
    path("backoffice/users/<int:pk>", UserDetailView.as_view(), name="user_detail"),
]
