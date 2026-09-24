from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    oud: str = Field(pattern=r"^\d{10}$")
    ico: str | None = Field(default=None, pattern=r"^\d{8}$")
    dic: str | None = Field(default=None, pattern=r"^\d{10}$")
    ic_dph: str | None = Field(default=None, pattern=r"^SK\d{10}$")


class SubjectUpdate(SubjectCreate):
    pass

class SubjectRead(SubjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class PaymentPreviewRequest(BaseModel):
    subject_id: int
    rule_id: str
    amount: str
    subject_type: str = "domestic_company"


class PaymentPreviewRead(BaseModel):
    subject_id: int
    subject_name: str
    oud: str
    rule_id: str
    rule_name: str
    amount: str
    currency: str
    domestic_account: str
    iban: str
    iban_valid: bool
    variable_symbol: str
    due_date: str | None
    due_date_basis: str | None = None
    source_url: str
    last_verified: str
    warning: str
