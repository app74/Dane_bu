import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


class UnsupportedTaxRule(ValueError):
    """Raised when no officially verified rule is safe to use."""


class InvalidRuleCatalog(ValueError):
    """Raised when a rule catalog misses mandatory audit data."""


@dataclass(frozen=True)
class TaxRule:
    id: str
    name: str
    valid_from: date
    valid_to: date | None
    status: str
    source_url: str
    last_verified: date
    data: dict

    @property
    def is_supported(self) -> bool:
        return self.status == "supported"

    def applies_on(self, on_date: date) -> bool:
        return self.valid_from <= on_date and (self.valid_to is None or on_date <= self.valid_to)


def load_rules(path: Path) -> tuple[TaxRule, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = []
    for raw in payload.get("rules", []):
        rules.append(
            TaxRule(
                id=raw["id"],
                name=raw["name"],
                valid_from=date.fromisoformat(raw["valid_from"]),
                valid_to=date.fromisoformat(raw["valid_to"]) if raw.get("valid_to") else None,
                status=raw["status"],
                source_url=raw["source_url"],
                last_verified=date.fromisoformat(raw["last_verified"]),
                data=raw,
            )
        )
    expanded = _expand_2026_period_rules(rules)
    validate_catalog(tuple(expanded))
    return tuple(expanded)


def _next_workday(value: date) -> date:
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def _expand_2026_period_rules(rules: list[TaxRule]) -> list[TaxRule]:
    """Expand official recurring 2026 templates into selectable periods."""
    result = list(rules)
    for template in rules:
        if template.status != "supported" or template.id not in {
            "income-po-advance-2026-month-01", "income-po-advance-2026-quarter-01",
            "vat-2026-month-03", "vat-2026-quarter-01",
        }:
            continue
        is_month = template.data["period_type"] == "month"
        periods = range(1, 13) if is_month else range(1, 5)
        for period in periods:
            rule_id = template.id[:-2] + f"{period:02d}"
            if any(item.id == rule_id for item in result):
                continue
            if is_month:
                start = date(2026, period, 1)
                end = (
                    date(2026, period + 1, 1) - timedelta(days=1)
                    if period < 12
                    else date(2026, 12, 31)
                )
                vs = f"1100{period:02d}2026"
                due = _next_workday(end)
                name_period = start.strftime("%B 2026")
            else:
                start_month = (period - 1) * 3 + 1
                start = date(2026, start_month, 1)
                end_month = start_month + 2
                end = (
                    date(2026, end_month + 1, 1) - timedelta(days=1)
                    if end_month < 12
                    else date(2026, 12, 31)
                )
                vs = f"1100{40 + period:02d}2026"
                due = _next_workday(end)
                name_period = ("I.", "II.", "III.", "IV.")[period - 1] + " štvrťrok 2026"
            data = dict(template.data)
            data.update(
                {
                    "id": rule_id,
                    "name": f"{template.name.split('–')[0].strip()} – {name_period}",
                    "valid_from": start.isoformat(),
                    "valid_to": end.isoformat(),
                    "vs": vs,
                    "due_date": due.isoformat(),
                }
            )
            result.append(TaxRule(
                id=rule_id, name=data["name"], valid_from=start, valid_to=end,
                status="supported", source_url=template.source_url,
                last_verified=template.last_verified, data=data,
            ))
    return result


def validate_catalog(rules: tuple[TaxRule, ...]) -> None:
    for rule in rules:
        if rule.valid_to is not None and rule.valid_to < rule.valid_from:
            raise InvalidRuleCatalog(f"Pravidlo {rule.id!r} má neplatný interval")
        if rule.is_supported:
            if not rule.source_url.startswith("https://www.financnasprava.sk/"):
                raise InvalidRuleCatalog(f"Pravidlo {rule.id!r} nemá oficiálny zdroj")
            if not rule.last_verified:
                raise InvalidRuleCatalog(f"Pravidlo {rule.id!r} nemá dátum overenia")
            if not rule.data.get("vs"):
                raise InvalidRuleCatalog(f"Pravidlo {rule.id!r} nemá VS")
            if not rule.data.get("account_prefix") and not rule.data.get(
                "account_prefix_by_subject"
            ):
                raise InvalidRuleCatalog(f"Pravidlo {rule.id!r} nemá predčíslie účtu")


def select_rule(rules: tuple[TaxRule, ...], rule_id: str, on_date: date) -> TaxRule:
    candidates = [rule for rule in rules if rule.id == rule_id and rule.applies_on(on_date)]
    if not candidates:
        raise UnsupportedTaxRule(f"Pravidlo {rule_id!r} nie je platné pre {on_date.isoformat()}")
    rule = candidates[0]
    if not rule.is_supported:
        raise UnsupportedTaxRule(f"Pravidlo {rule_id!r} nie je potvrdené pre produkčné použitie")
    return rule
