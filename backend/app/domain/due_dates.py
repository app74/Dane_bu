"""Due-date computation for tax periods. Pure functions, no database or HTTP."""

from calendar import monthrange
from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, timedelta

CATALOG = "catalog"
NEXT_MONTH_DAY = "next_month_day"
PERIOD_END = "period_end"
KINDS = (CATALOG, NEXT_MONTH_DAY, PERIOD_END)


@dataclass(frozen=True)
class DueDateRule:
    kind: str
    day: int | None = None
    shift_to_workday: bool = True

    def describe(self) -> str:
        if self.kind == NEXT_MONTH_DAY:
            text = f"{self.day}. deň mesiaca nasledujúceho po skončení obdobia"
        elif self.kind == PERIOD_END:
            text = "posledný deň obdobia"
        else:
            return "dátum z oficiálneho číselníka"
        if self.shift_to_workday:
            text += "; sobota, nedeľa alebo sviatok sa posúva na najbližší pracovný deň"
        return text


def easter_sunday(year: int) -> date:
    """Gregorian Easter Sunday (anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month, day = divmod(h + l_ - 7 * m + 114, 31)
    return date(year, month, day + 1)


def next_workday(value: date, holidays: Collection[date]) -> date:
    while value.weekday() >= 5 or value in holidays:
        value += timedelta(days=1)
    return value


def compute_due_date(
    rule: DueDateRule,
    period_end: date | None,
    catalog_due: date | None,
    holidays: Collection[date] = (),
) -> date | None:
    """Return the due date, or None when it cannot be determined safely."""
    if rule.kind == CATALOG or period_end is None:
        return catalog_due
    if rule.kind == NEXT_MONTH_DAY:
        if rule.day is None or not 1 <= rule.day <= 31:
            raise ValueError("Deň splatnosti musí byť 1 až 31.")
        year = period_end.year + (period_end.month == 12)
        month = period_end.month % 12 + 1
        due = date(year, month, min(rule.day, monthrange(year, month)[1]))
    elif rule.kind == PERIOD_END:
        due = period_end
    else:
        raise ValueError(f"Neznámy typ pravidla splatnosti: {rule.kind}")
    return next_workday(due, holidays) if rule.shift_to_workday else due
