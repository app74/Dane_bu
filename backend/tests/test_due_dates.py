"""Due dates: independent calendar facts, not a re-run of the implementation."""

from datetime import date

import pytest

from app.domain.due_dates import (
    CATALOG,
    NEXT_MONTH_DAY,
    PERIOD_END,
    DueDateRule,
    compute_due_date,
    easter_sunday,
    next_workday,
)

VAT = DueDateRule(NEXT_MONTH_DAY, day=25, shift_to_workday=True)
# Slovak days of rest used in the scenarios below (zákon 241/1993 Z.z.).
HOLIDAYS_2026 = {
    date(2026, 4, 3), date(2026, 4, 6),  # Veľký piatok, Veľkonočný pondelok
    date(2026, 12, 24), date(2026, 12, 25), date(2026, 12, 26),
}


@pytest.mark.parametrize(("year", "expected"), [
    (2024, date(2024, 3, 31)), (2025, date(2025, 4, 20)),
    (2026, date(2026, 4, 5)), (2027, date(2027, 3, 28)), (2028, date(2028, 4, 16)),
])
def test_easter_sunday_matches_published_dates(year, expected) -> None:
    assert easter_sunday(year) == expected


@pytest.mark.parametrize(("period_end", "expected"), [
    (date(2026, 8, 31), date(2026, 9, 25)),   # August: 25.9.2026 is a Friday
    (date(2026, 3, 31), date(2026, 4, 27)),   # 25.4.2026 Saturday -> Monday (FS list: 27.04.2026)
    (date(2026, 9, 30), date(2026, 10, 26)),  # 25.10.2026 Sunday -> Monday
    (date(2026, 11, 30), date(2026, 12, 28)), # 25.12. Fri holiday, 26.12. Sat, 27.12. Sun
    (date(2026, 12, 31), date(2027, 1, 25)),  # December -> next year, Monday
])
def test_vat_month_is_25th_of_next_month_shifted_to_workday(period_end, expected) -> None:
    assert compute_due_date(VAT, period_end, None, HOLIDAYS_2026) == expected


def test_vat_quarter_uses_month_after_quarter_end() -> None:
    assert compute_due_date(VAT, date(2026, 6, 30), None, HOLIDAYS_2026) == date(2026, 7, 27)


def test_holiday_on_25th_moves_to_next_workday() -> None:
    # Hypothetical holiday on Thursday 25.3.2027, then Good Friday 26.3. and Easter Monday 29.3.
    holidays = {date(2027, 3, 25), date(2027, 3, 26), date(2027, 3, 29)}
    assert compute_due_date(VAT, date(2027, 2, 28), None, holidays) == date(2027, 3, 30)


def test_without_shift_keeps_weekend_date() -> None:
    rule = DueDateRule(NEXT_MONTH_DAY, day=25, shift_to_workday=False)
    assert compute_due_date(rule, date(2026, 3, 31), None) == date(2026, 4, 25)


def test_day_is_clamped_to_month_length() -> None:
    rule = DueDateRule(NEXT_MONTH_DAY, day=31, shift_to_workday=False)
    assert compute_due_date(rule, date(2026, 1, 31), None) == date(2026, 2, 28)


def test_period_end_rule_for_advances() -> None:
    rule = DueDateRule(PERIOD_END, shift_to_workday=True)
    assert compute_due_date(rule, date(2026, 1, 31), None) == date(2026, 2, 2)  # FS: 02.02.2026


def test_catalog_rule_keeps_official_date() -> None:
    rule = DueDateRule(CATALOG)
    assert compute_due_date(rule, date(2025, 12, 31), date(2026, 3, 31)) == date(2026, 3, 31)
    assert compute_due_date(rule, None, None) is None


def test_invalid_day_is_rejected() -> None:
    with pytest.raises(ValueError):
        compute_due_date(DueDateRule(NEXT_MONTH_DAY, day=0), date(2026, 1, 31), None)


def test_next_workday_skips_weekend_and_holidays() -> None:
    assert next_workday(date(2026, 12, 24), HOLIDAYS_2026) == date(2026, 12, 28)
    assert next_workday(date(2026, 9, 25), HOLIDAYS_2026) == date(2026, 9, 25)
