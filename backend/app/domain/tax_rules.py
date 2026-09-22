import json
from dataclasses import dataclass
from datetime import date
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
    validate_catalog(tuple(rules))
    return tuple(rules)


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
