from decimal import Decimal

import pytest

from app.domain.payment_symbols import monthly_vs, quarterly_vs, validate_vs
from app.domain.values import EuroAmount, TaxPeriod


def test_confirmed_vs_patterns() -> None:
    assert monthly_vs("1100", 2026, 1) == "1100012026"
    assert quarterly_vs("1100", 2026, 2) == "1100422026"
    assert validate_vs("1700992025") == "1700992025"


@pytest.mark.parametrize("value", ["110012026", "abc0992025", "11009920260"])
def test_vs_requires_ten_digits(value: str) -> None:
    with pytest.raises(ValueError):
        validate_vs(value)


def test_decimal_amount_never_uses_float() -> None:
    amount = EuroAmount.parse("123,45")
    assert amount.value == Decimal("123.45")


def test_period_is_unambiguous() -> None:
    assert TaxPeriod(year=2026, month=1).month == 1
    with pytest.raises(ValueError):
        TaxPeriod(year=2026, month=1, quarter=1)
