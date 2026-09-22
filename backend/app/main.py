import json
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .domain.iban import domestic_account, slovak_iban, validate_iban
from .domain.payment_symbols import validate_vs
from .domain.tax_rules import UnsupportedTaxRule, load_rules, select_rule
from .domain.values import EuroAmount
from .models import PaymentInstruction, Subject
from .schemas import (
    PaymentPreviewRead,
    PaymentPreviewRequest,
    SubjectCreate,
    SubjectRead,
    SubjectUpdate,
)

app = FastAPI(title="Platobné údaje pre dane", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
RULES_PATH = Path(__file__).parents[2] / "docs" / "tax-rules.json"
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tax-rules")
def tax_rules() -> list[dict[str, str | None]]:
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "valid_from": rule.valid_from.isoformat(),
            "valid_to": rule.valid_to.isoformat() if rule.valid_to else None,
            "source_url": rule.source_url,
            "last_verified": rule.last_verified.isoformat(),
        }
        for rule in load_rules(RULES_PATH)
        if rule.is_supported
    ]

@app.post("/subjects", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)) -> Subject:
    subject = Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

@app.get("/subjects", response_model=list[SubjectRead])
def list_subjects(db: Session = Depends(get_db)) -> list[Subject]:
    return list(db.query(Subject).order_by(Subject.id).all())

@app.get("/subjects/{subject_id}", response_model=SubjectRead)
def get_subject(subject_id: int, db: Session = Depends(get_db)) -> Subject:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subjekt neexistuje")
    return subject


@app.put("/subjects/{subject_id}", response_model=SubjectRead)
def update_subject(
    subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db)
) -> Subject:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subjekt neexistuje")
    for key, value in payload.model_dump().items():
        setattr(subject, key, value)
    db.commit()
    db.refresh(subject)
    return subject


@app.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db)) -> None:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subjekt neexistuje")
    db.delete(subject)
    db.commit()


@app.post("/payment-instructions/preview", response_model=PaymentPreviewRead)
def preview_payment(
    payload: PaymentPreviewRequest, db: Session = Depends(get_db)
) -> PaymentPreviewRead:
    subject = db.get(Subject, payload.subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subjekt neexistuje")
    try:
        amount = EuroAmount.parse(payload.amount)
        if payload.rule_id.startswith("vat-"):
            selection_date = date(2026, 3, 31)
        elif payload.rule_id.startswith("income-po-advance-"):
            selection_date = date(2026, 1, 31)
        elif payload.rule_id.startswith("withholding-dividend-"):
            selection_date = date(2026, 5, 31)
        else:
            selection_date = date(2025, 12, 31)
        rule = select_rule(load_rules(RULES_PATH), payload.rule_id, selection_date)
    except (ValueError, UnsupportedTaxRule) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if rule.id == "income-return-2025":
        try:
            prefix = rule.data["account_prefix_by_subject"][payload.subject_type]
        except KeyError as error:
            raise HTTPException(status_code=422, detail="Nepodporovaný typ subjektu") from error
        variable_symbol = validate_vs(rule.data["vs"])
        due_date = rule.data.get("due_date")
    elif rule.id == "motor-vehicle-return-2025":
        prefix = rule.data["account_prefix"]
        variable_symbol = validate_vs(rule.data["vs"])
        due_date = rule.data.get("due_date")
    elif rule.id.startswith("income-fo-"):
        prefix = rule.data["account_prefix"]
        variable_symbol = validate_vs(rule.data["vs"])
        due_date = rule.data.get("due_date")
    elif rule.id.startswith("income-po-advance-"):
        prefix = rule.data["account_prefix"]
        variable_symbol = validate_vs(rule.data["vs"])
        due_date = rule.data.get("due_date")
    elif rule.id.startswith("vat-"):
        prefix = rule.data["account_prefix"]
        variable_symbol = validate_vs(rule.data["vs"])
        due_date = rule.data.get("due_date")
    elif rule.id.startswith("withholding-dividend-"):
        prefix = rule.data["account_prefix"]
        variable_symbol = validate_vs(rule.data["vs"])
        due_date = rule.data.get("due_date")
    else:
        raise HTTPException(status_code=422, detail="Pravidlo zatiaľ nemá bezpečný výpočet")
    return PaymentPreviewRead(
        subject_id=subject.id,
        subject_name=subject.name,
        oud=subject.oud,
        rule_id=rule.id,
        rule_name=rule.name,
        amount=str(amount.value),
        currency="EUR",
        domestic_account=domestic_account(prefix, subject.oud),
        iban=slovak_iban(prefix, subject.oud),
        iban_valid=validate_iban(slovak_iban(prefix, subject.oud)),
        variable_symbol=variable_symbol,
        due_date=due_date,
        source_url=rule.source_url,
        last_verified=rule.last_verified.isoformat(),
        warning=(
            "Pred úhradou porovnajte údaje s oficiálnymi platobnými inštrukciami "
            "Finančnej správy SR."
        ),
    )


@app.post(
    "/payment-instructions",
    response_model=PaymentPreviewRead,
    status_code=status.HTTP_201_CREATED,
)
def save_payment_instruction(
    payload: PaymentPreviewRequest, db: Session = Depends(get_db)
) -> PaymentPreviewRead:
    preview = preview_payment(payload, db)
    record = PaymentInstruction(
        subject_id=preview.subject_id,
        rule_id=preview.rule_id,
        snapshot_json=preview.model_dump_json(),
    )
    db.add(record)
    db.commit()
    return preview


@app.get("/payment-instructions", response_model=list[PaymentPreviewRead])
def list_payment_instructions(db: Session = Depends(get_db)) -> list[PaymentPreviewRead]:
    records = db.query(PaymentInstruction).order_by(PaymentInstruction.id.desc()).all()
    return [
        PaymentPreviewRead.model_validate(json.loads(record.snapshot_json)) for record in records
    ]


@app.get("/payment-instructions/{instruction_id}", response_model=PaymentPreviewRead)
def get_payment_instruction(
    instruction_id: int, db: Session = Depends(get_db)
) -> PaymentPreviewRead:
    record = db.get(PaymentInstruction, instruction_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Platobná inštrukcia neexistuje")
    return PaymentPreviewRead.model_validate(json.loads(record.snapshot_json))
