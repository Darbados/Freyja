from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from users.models import FreyjaUser


@method_decorator(staff_member_required, name="dispatch")
class UserListView(ListView):
    """Lists Freyja users for backoffice staff."""

    context_object_name = "users"
    model = FreyjaUser
    paginate_by = 50
    template_name = "backoffice/users_admin/user_list.html"

    def get_queryset(self):
        return FreyjaUser.objects.only(
            "email",
            "date_joined",
            "email_confirmed_at",
        ).order_by("-date_joined", "-pk")


@method_decorator(staff_member_required, name="dispatch")
class UserDetailView(DetailView):
    """Displays a Freyja user's account details to backoffice staff."""

    context_object_name = "user_record"
    model = FreyjaUser
    template_name = "backoffice/users_admin/user_detail.html"
