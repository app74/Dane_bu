from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = tuple(
        Index(f"uq_subjects_{field}", field, unique=True)
        for field in ("oud", "ico", "dic", "ic_dph")
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    oud: Mapped[str] = mapped_column(String(10))
    ico: Mapped[str | None] = mapped_column(String(8), nullable=True)
    dic: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ic_dph: Mapped[str | None] = mapped_column(String(12), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class PaymentInstruction(Base):
    __tablename__ = "payment_instructions"
    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column()
    rule_id: Mapped[str] = mapped_column(String(100))
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class DueDateSetting(Base):
    """User-editable due-date rule per group of confirmed tax rules (see app/due_settings.py)."""

    __tablename__ = "due_date_settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shift_to_workday: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class PublicHoliday(Base):
    """Non-working days (besides weekends) used to shift due dates."""

    __tablename__ = "public_holidays"
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
