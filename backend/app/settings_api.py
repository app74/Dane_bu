"""Settings API: due-date rules per rule group and the non-working days table."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from .db import get_db
from .domain.due_dates import KINDS, NEXT_MONTH_DAY
from .due_settings import GROUPS, GROUPS_BY_KEY, HOLIDAYS_SOURCE, load_rule
from .models import DueDateSetting, PublicHoliday

router = APIRouter(prefix="/settings")


class DueDateSettingUpdate(BaseModel):
    kind: str
    day: int | None = Field(default=None, ge=1, le=31)
    shift_to_workday: bool = True

    @model_validator(mode="after")
    def check(self) -> "DueDateSettingUpdate":
        if self.kind not in KINDS:
            raise ValueError("Neznámy typ pravidla splatnosti.")
        if self.kind == NEXT_MONTH_DAY and self.day is None:
            raise ValueError("Zadajte deň splatnosti (1 až 31).")
        if self.kind != NEXT_MONTH_DAY:
            self.day = None
        return self


class HolidayCreate(BaseModel):
    day: date
    name: str = Field(min_length=1, max_length=100)


def _setting_view(db: Session, key: str) -> dict:
    group = GROUPS_BY_KEY[key]
    rule = load_rule(db, group)
    return {
        "key": group.key,
        "label": group.label,
        "kind": rule.kind,
        "day": rule.day,
        "shift_to_workday": rule.shift_to_workday,
        "description": rule.describe(),
        "basis": group.basis,
        "is_default": db.get(DueDateSetting, key) is None,
    }


@router.get("/due-dates")
def list_due_date_settings(db: Session = Depends(get_db)) -> list[dict]:
    return [_setting_view(db, group.key) for group in GROUPS]


@router.put("/due-dates/{key}")
def update_due_date_setting(
    key: str, payload: DueDateSettingUpdate, db: Session = Depends(get_db)
) -> dict:
    if key not in GROUPS_BY_KEY:
        raise HTTPException(404, "Neznáma skupina pravidiel.")
    row = db.get(DueDateSetting, key) or DueDateSetting(key=key)
    row.kind, row.day, row.shift_to_workday = payload.kind, payload.day, payload.shift_to_workday
    db.add(row)
    db.commit()
    return _setting_view(db, key)


@router.delete("/due-dates/{key}")
def reset_due_date_setting(key: str, db: Session = Depends(get_db)) -> dict:
    if key not in GROUPS_BY_KEY:
        raise HTTPException(404, "Neznáma skupina pravidiel.")
    row = db.get(DueDateSetting, key)
    if row is not None:
        db.delete(row)
        db.commit()
    return _setting_view(db, key)


@router.get("/holidays")
def list_holidays(year: int | None = None, db: Session = Depends(get_db)) -> dict:
    query = db.query(PublicHoliday).order_by(PublicHoliday.day)
    rows = [row for row in query if year is None or row.day.year == year]
    return {
        "source_url": HOLIDAYS_SOURCE,
        "holidays": [{"day": row.day.isoformat(), "name": row.name} for row in rows],
    }


@router.post("/holidays", status_code=status.HTTP_201_CREATED)
def add_holiday(payload: HolidayCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(PublicHoliday, payload.day) is not None:
        raise HTTPException(409, "Tento deň už je v zozname.")
    db.add(PublicHoliday(day=payload.day, name=payload.name.strip()))
    db.commit()
    return {"day": payload.day.isoformat(), "name": payload.name.strip()}


@router.delete("/holidays/{day}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(day: date, db: Session = Depends(get_db)) -> None:
    row = db.get(PublicHoliday, day)
    if row is None:
        raise HTTPException(404, "Deň nie je v zozname.")
    db.delete(row)
    db.commit()
