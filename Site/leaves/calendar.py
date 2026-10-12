"""Bulgarian working days for the supported Monday-Friday leave calendar."""

import datetime
from functools import lru_cache

import holidays


@lru_cache(maxsize=32)
def public_holidays(year: int) -> frozenset[datetime.date]:
    return frozenset(holidays.country_holidays("BG", years=year, observed=True))


def is_working_day(day: datetime.date) -> bool:
    return day.weekday() < 5 and day not in public_holidays(day.year)


def working_dates(start: datetime.date, end: datetime.date) -> list[datetime.date]:
    return [
        day
        for offset in range((end - start).days + 1)
        if is_working_day(day := start + datetime.timedelta(days=offset))
    ]
