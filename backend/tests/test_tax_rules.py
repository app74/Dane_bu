from datetime import date
from pathlib import Path

import pytest

from app.domain.tax_rules import InvalidRuleCatalog, UnsupportedTaxRule, load_rules, select_rule

RULES = Path(__file__).parents[2] / "docs" / "tax-rules.json"


def test_loads_verified_income_rule() -> None:
    rule = select_rule(load_rules(RULES), "income-return-2025", date(2025, 12, 31))
    assert rule.data["vs"] == "1700992025"
    assert rule.source_url.startswith("https://www.financnasprava.sk/")


def test_rejects_unverified_rule() -> None:
    with pytest.raises(UnsupportedTaxRule):
        select_rule(load_rules(RULES), "vat-2026-monthly", date(2026, 1, 31))


def test_rejects_out_of_validity_period() -> None:
    with pytest.raises(UnsupportedTaxRule):
        select_rule(load_rules(RULES), "income-return-2025", date(2026, 1, 1))


def test_catalog_rejects_supported_rule_without_official_source(tmp_path: Path) -> None:
    invalid = tmp_path / "rules.json"
    invalid.write_text(
        '{"rules":[{"id":"bad","name":"Bad","valid_from":"2025-01-01",'
        '"status":"supported","source_url":"https://example.com",'
        '"last_verified":"2025-01-01","vs":"1700992025",'
        '"account_prefix":"500224"}]}',
        encoding="utf-8",
    )
    with pytest.raises(InvalidRuleCatalog):
        load_rules(invalid)
