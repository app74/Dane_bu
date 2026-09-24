"""Due-date settings: groups of confirmed tax rules, their defaults and non-working days.

Defaults live here; a row in due_date_settings (edited in the UI) overrides them.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .domain.due_dates import CATALOG, NEXT_MONTH_DAY, PERIOD_END, DueDateRule, easter_sunday
from .models import DueDateSetting, PublicHoliday

VAT_BASIS = "https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2004/222/"
HOLIDAYS_SOURCE = "https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/1993/241/"


@dataclass(frozen=True)
class DueGroup:
    key: str
    label: str
    prefixes: tuple[str, ...]
    default: DueDateRule
    basis: str


GROUPS = (
    DueGroup("vat-month", "DPH – mesačný platiteľ", ("vat-2026-month-",),
             DueDateRule(NEXT_MONTH_DAY, 25, True),
             f"§ 78 ods. 1 zákona č. 222/2004 Z.z. (do 25 dní po skončení obdobia) – {VAT_BASIS}"),
    DueGroup("vat-quarter", "DPH – štvrťročný platiteľ", ("vat-2026-quarter-",),
             DueDateRule(NEXT_MONTH_DAY, 25, True),
             f"§ 78 ods. 1 zákona č. 222/2004 Z.z. (do 25 dní po skončení obdobia) – {VAT_BASIS}"),
    DueGroup("po-advance-month", "Preddavok DPPO – mesačný", ("income-po-advance-2026-month-",),
             DueDateRule(PERIOD_END, None, True),
             "Oficiálny zoznam VS Finančnej správy SR (splatnosť k poslednému dňu mesiaca)"),
    DueGroup("po-advance-quarter", "Preddavok DPPO – štvrťročný",
             ("income-po-advance-2026-quarter-",), DueDateRule(PERIOD_END, None, True),
             "Oficiálny zoznam VS Finančnej správy SR (splatnosť k poslednému dňu štvrťroka)"),
    DueGroup("income-return", "Daň z príjmov z priznania", ("income-return-", "income-fo-"),
             DueDateRule(CATALOG), "Dátum z oficiálneho číselníka (docs/tax-rules.json)"),
    DueGroup("motor-vehicle", "Daň z motorových vozidiel", ("motor-vehicle-",),
             DueDateRule(CATALOG), "Dátum z oficiálneho číselníka (docs/tax-rules.json)"),
    DueGroup("withholding", "Zrážková daň", ("withholding-",),
             DueDateRule(CATALOG), "Dátum z oficiálneho číselníka (docs/tax-rules.json)"),
)
GROUPS_BY_KEY = {group.key: group for group in GROUPS}


def group_for(rule_id: str) -> DueGroup | None:
    return next((g for g in GROUPS if rule_id.startswith(g.prefixes)), None)


def load_rule(db: Session, group: DueGroup) -> DueDateRule:
    row = db.get(DueDateSetting, group.key)
    if row is None:
        return group.default
    return DueDateRule(row.kind, row.day, row.shift_to_workday)


def holiday_dates(db: Session) -> set[date]:
    return {row.day for row in db.query(PublicHoliday)}


def default_holidays(year: int) -> list[tuple[date, str]]:
    """Days of rest confirmed by zákon č. 241/1993 Z.z. and Úrad vlády SR (verified 2026-09-24).

    Deliberately left out because the sources differ or § 4b excludes them for 2026:
    1.9., 28.10., 17.11. (state holidays with disputed day-of-rest status), 8.5. and 15.9.
    Add them in Nastavenia → Sviatky after checking the current text of the act.
    """
    easter = easter_sunday(year)
    return sorted([
        (date(year, 1, 1), "Deň vzniku Slovenskej republiky"),
        (date(year, 1, 6), "Zjavenie Pána"),
        (easter - timedelta(days=2), "Veľký piatok"),
        (easter + timedelta(days=1), "Veľkonočný pondelok"),
        (date(year, 5, 1), "Sviatok práce"),
        (date(year, 7, 5), "Sviatok svätého Cyrila a svätého Metoda"),
        (date(year, 8, 29), "Výročie Slovenského národného povstania"),
        (date(year, 11, 1), "Sviatok Všetkých svätých"),
        (date(year, 12, 24), "Štedrý deň"),
        (date(year, 12, 25), "Prvý sviatok vianočný"),
        (date(year, 12, 26), "Druhý sviatok vianočný"),
    ])
