from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING

from django.db.models import Q

from employment.models import Employee, Employment
from leaves.models import Leave


def annual_leave_balance(employee: Employee, year: int) -> dict[str, Decimal | int]:
    """Calculates the employee's booked and remaining annual leave for one year."""

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    employment = (
        Employment.objects.select_related("employment_type")
        .filter(employee=employee, start_date__lte=year_end)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=year_start))
        .order_by("-start_date", "-id")
        .first()
    )

    entitlement = 0
    if employment and employment.employment_type.paid_leave_eligible:
        if employment.base_leave_days_override is not None:
            entitlement = _round_entitlement_up(employment.base_leave_days_override)
        else:
            eligible_months = 12
            if employment.start_date.year == year:
                eligible_months = 13 - employment.start_date.month
            monthly_entitlement = (
                employment.employment_type.default_base_leave_days
                * Decimal(eligible_months)
                / Decimal("12")
            )
            entitlement = _round_entitlement_up(monthly_entitlement)

    booked_requests = employee.leave_requests.filter(
        leave_type=Leave.LeaveType.ANNUAL,
        status__in=(Leave.Status.PENDING, Leave.Status.APPROVED),
        start_date__lte=year_end,
        end_date__gte=year_start,
    )
    booked = sum(
        (_leave_days_in_period(leave, year_start, year_end) for leave in booked_requests),
        Decimal("0"),
    )
    return {
        "year": year,
        "entitlement_days": entitlement,
        "booked_days": booked,
        "remaining_days": max(Decimal("0"), Decimal(entitlement) - booked),
    }


def _round_entitlement_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_CEILING))


def _leave_days_in_period(leave: Leave, period_start: date, period_end: date) -> Decimal:
    start = max(leave.start_date, period_start)
    end = min(leave.end_date, period_end)
    if end < start:
        return Decimal("0")

    workdays = sum(
        1
        for offset in range((end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() < 5
    )
    days = Decimal(workdays)
    if days == 0:
        return days

    if start == end:
        if leave.start_date == leave.end_date:
            return Decimal("1") if leave.start_day_part == Leave.DayPart.FULL_DAY else Decimal("0.5")
        if start == leave.start_date and leave.start_day_part == Leave.DayPart.SECOND_HALF:
            return Decimal("0.5")
        if end == leave.end_date and leave.end_day_part == Leave.DayPart.FIRST_HALF:
            return Decimal("0.5")
        return Decimal("1")

    if start == leave.start_date and leave.start_day_part == Leave.DayPart.SECOND_HALF:
        days -= Decimal("0.5")
    if end == leave.end_date and leave.end_day_part == Leave.DayPart.FIRST_HALF:
        days -= Decimal("0.5")
    return days
