"""Create immutable snapshots and render persisted document jobs."""

import hashlib
import json
import logging
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from employment.models import Employee, Employment, RelationshipKind
from Freyja.mailer import Mailer
from leaves.calendar import working_dates
from leaves.models import Leave, LeaveDocument
from leaves.pdf import render_annual_request

logger = logging.getLogger(__name__)


class RequestConflict(APIException):
    status_code = 409
    default_detail = "This submission ID belongs to a different request. Start a new submission."


def submission_hash(data: dict) -> str:
    values = {key: value for key, value in data.items() if key != "client_request_id"}
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()


def document_snapshot(employee: Employee, leave: Leave, digest: str) -> tuple[Employment, dict]:
    employments = list(
        Employment.objects.select_related("employment_type", "employer")
        .filter(employee=employee, start_date__lte=leave.start_date)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=leave.end_date))[:2]
    )
    if len(employments) != 1:
        raise ValidationError({"detail": "Ask HR to assign one employment covering this period."})
    employment = employments[0]
    if (
        employment.employment_type.relationship_kind != RelationshipKind.EMPLOYMENT
        or not employment.employment_type.paid_leave_eligible
        or not employment.uses_bulgarian_leave_calendar
    ):
        raise ValidationError(
            {
                "detail": "This template requires eligible Bulgarian employment and a confirmed "
                "Monday-Friday calendar. Ask HR to review your employment."
            }
        )
    if not employment.employer_id or not all(
        (employee.legal_name.strip(), employee.personnel_number.strip(), employee.job_title.strip())
    ):
        raise ValidationError(
            {
                "detail": "Ask HR to complete your employer, full legal name, personnel number "
                "and job title before requesting annual leave."
            }
        )
    employer = employment.employer
    dates = working_dates(leave.start_date, leave.end_date)
    return employment, {
        "employer_name": employer.legal_name,
        "employer_eik": employer.eik,
        "addressee": employer.addressee,
        "employee_name": employee.legal_name,
        "personnel_number": employee.personnel_number,
        "job_title": employee.job_title,
        "start_date": leave.start_date.isoformat(),
        "end_date": leave.end_date.isoformat(),
        "working_dates": [day.isoformat() for day in dates],
        "working_days": len(dates),
        "prepared_date": timezone.localdate(timezone=ZoneInfo("Europe/Sofia")).isoformat(),
        "submission_hash": digest,
    }


@transaction.atomic
def create_leave_request(employee_id: int, data: dict) -> tuple[Leave, bool]:
    # Serializes duplicate submissions by this employee before checking the unique key.
    employee = Employee.objects.select_for_update().get(pk=employee_id)
    request_id = data.get("client_request_id")
    digest = submission_hash(data)
    if request_id:
        existing = employee.leave_requests.filter(client_request_id=request_id).first()
        if existing:
            original = {key: getattr(existing, key) for key in data if key != "client_request_id"}
            expected = (
                existing.document.snapshot["submission_hash"]
                if hasattr(existing, "document")
                else submission_hash(original)
            )
            if expected != digest:
                raise RequestConflict()
            return existing, False

    approver = employee.leave_approver or employee.manager
    if approver is None:
        raise ValidationError(
            {"approver": "No manager or leave approver is assigned to your profile."}
        )
    leave = Leave(employee=employee, approver=approver, **data)
    annual = leave.leave_type == Leave.LeaveType.ANNUAL
    if annual:
        employment, snapshot = document_snapshot(employee, leave, digest)
    leave.save()
    if annual:
        document = LeaveDocument.objects.create(
            leave=leave, employment=employment, snapshot=snapshot
        )
        transaction.on_commit(lambda: generate_document(document.pk))
    transaction.on_commit(lambda: Mailer().send_leave_request(leave))
    return leave, True


@transaction.atomic
def generate_document(document_id) -> LeaveDocument:
    # The row itself is the durable job. A crash rolls back to pending/failed;
    # the command or retry endpoint can safely resume it with the same snapshot.
    document = LeaveDocument.objects.select_for_update().get(pk=document_id)
    if document.state == LeaveDocument.State.READY:
        return document
    updates = {"attempts": document.attempts + 1, "updated_at": timezone.now()}
    try:
        pdf = render_annual_request(document)
        updates.update(
            pdf=pdf,
            sha256=hashlib.sha256(pdf).hexdigest(),
            generated_at=timezone.now(),
            state=LeaveDocument.State.READY,
        )
    except Exception:
        # Do not expose renderer internals or personal data in the API error.
        logger.exception("Leave document rendering failed: %s", document.pk)
        updates["state"] = LeaveDocument.State.FAILED
    LeaveDocument.objects.filter(pk=document.pk).update(**updates)
    document.refresh_from_db()
    return document
