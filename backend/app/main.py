import csv
import io
import json
import os
from datetime import date
from pathlib import Path

from fastapi import Body, Depends, FastAPI, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth
from .db import IS_SQLITE, Base, engine, get_db
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
from .subject_identity import matching_subjects, same_subject
from .subject_lookup import LookupUnavailable, fs_lookup_enabled, lookup_subject


def cors_origins() -> list[str]:
    """Local Vite origins plus e.g. CORS_ORIGINS=http://192.168.10.132:5173 for LAN access."""
    extra = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",")]
    return ["http://localhost:5173", "http://127.0.0.1:5173", *filter(None, extra)]


app = FastAPI(title="Platobné údaje pre dane", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)
auth.install(app)


def rules_path() -> Path:
    configured = os.getenv("TAX_RULES_PATH")
    if configured:
        return Path(configured)
    here = Path(__file__).resolve()
    # Repository/Docker layout first, then the copy made by the Vercel build step.
    candidates = [here.parents[2] / "docs" / "tax-rules.json",
                  here.parents[1] / "docs" / "tax-rules.json"]
    return next((path for path in candidates if path.exists()), candidates[0])


RULES_PATH = rules_path()
if IS_SQLITE:
    # Hosted Postgres is managed only by Alembic migrations.
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
def create_subject(
    payload: SubjectCreate, response: Response, db: Session = Depends(get_db)
) -> Subject:
    existing = matching_subjects(db, payload)
    if existing:
        if len(existing) == 1 and same_subject(existing[0], payload):
            response.status_code = status.HTTP_200_OK
            return existing[0]
        raise HTTPException(
            409,
            "Subjekt s týmto OÚD alebo identifikátorom už existuje. "
            "Vyberte ho zo zoznamu a použite Upraviť subjekt.",
        )
    subject = Subject(**payload.model_dump())
    db.add(subject)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        existing = matching_subjects(db, payload)
        if len(existing) == 1 and same_subject(existing[0], payload):
            response.status_code = status.HTTP_200_OK
            return existing[0]
        raise HTTPException(
            409, "Subjekt s týmto OÚD alebo identifikátorom už existuje."
        ) from error
    db.refresh(subject)
    return subject

@app.get("/subjects", response_model=list[SubjectRead])
def list_subjects(db: Session = Depends(get_db)) -> list[Subject]:
    return list(db.query(Subject).order_by(Subject.id).all())


@app.get("/subjects.csv")
def export_subjects(db: Session = Depends(get_db)) -> StreamingResponse:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["name", "oud", "ico", "dic", "ic_dph"])
    for subject in db.query(Subject).order_by(Subject.id):
        writer.writerow([
            subject.name, subject.oud, subject.ico or "", subject.dic or "", subject.ic_dph or ""
        ])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=subjekty.csv"
    })


@app.post("/subjects/import/preview")
async def preview_subject_import(file: UploadFile) -> dict:
    try:
        text = (await file.read()).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows, errors = [], []
        for number, row in enumerate(reader, 2):
            try:
                item = SubjectCreate(**{key: (row.get(key) or None) for key in (
                    "name", "oud", "ico", "dic", "ic_dph")})
                rows.append(item.model_dump())
            except Exception as error:
                errors.append({"row": number, "error": str(error)})
        return {"rows": rows, "errors": errors, "valid": not errors and bool(rows)}
    except UnicodeDecodeError as error:
        raise HTTPException(422, "CSV musí byť v UTF-8.") from error


@app.post("/subjects/import")
async def import_subjects(file: UploadFile, db: Session = Depends(get_db)) -> dict:
    await file.seek(0)
    preview = await preview_subject_import(file)
    if not preview["valid"]:
        raise HTTPException(422, detail=preview)
    created = 0
    for values in preview["rows"]:
        payload = SubjectCreate(**values)
        existing = matching_subjects(db, payload)
        if existing:
            if len(existing) == 1 and same_subject(existing[0], payload):
                continue
            raise HTTPException(409, "CSV obsahuje konflikt identifikátorov.")
        db.add(Subject(**values))
        created += 1
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "CSV obsahuje duplicitný identifikátor.") from error
    return {"created": created, "skipped": len(preview["rows"]) - created}

@app.post("/subject-lookup")
def subject_lookup(identifier: str = Body(embed=True, max_length=200)) -> dict:
    if not fs_lookup_enabled():
        raise HTTPException(
            status_code=503,
            detail="Vyhľadanie v exportoch FS je v tomto nasadení vypnuté. "
            "Zadajte OÚD ručne a overte ho na portáli Finančnej správy.",
        )
    try:
        return lookup_subject(identifier)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LookupUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


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
    if any(item.id != subject_id for item in matching_subjects(db, payload)):
        raise HTTPException(409, "Iný subjekt s týmto OÚD alebo identifikátorom už existuje.")
    for key, value in payload.model_dump().items():
        setattr(subject, key, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            409, "Iný subjekt s týmto OÚD alebo identifikátorom už existuje."
        ) from error
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
        if payload.rule_id.startswith("vat-") or payload.rule_id.startswith("income-po-advance-"):
            parts = payload.rule_id.rsplit("-", 2)
            period = int(parts[-1])
            selection_date = (
                date(2026, period, 28)
                if parts[-2] == "month"
                else date(2026, period * 3, 28)
            )
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
