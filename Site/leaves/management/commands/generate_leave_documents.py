from django.core.management.base import BaseCommand

from leaves.documents import generate_document
from leaves.models import LeaveDocument


class Command(BaseCommand):
    help = "Retry pending or failed leave PDF jobs using their original snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        ids = list(
            LeaveDocument.objects.exclude(state=LeaveDocument.State.READY)
            .order_by("updated_at")
            .values_list("pk", flat=True)[: max(0, options["limit"])]
        )
        for document_id in ids:
            document = generate_document(document_id)
            self.stdout.write(f"{document_id}: {document.state}")
