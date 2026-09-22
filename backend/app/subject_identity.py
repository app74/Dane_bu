from sqlalchemy import or_
from sqlalchemy.orm import Session

from .models import Subject
from .schemas import SubjectCreate

IDENTIFIERS = ("oud", "ico", "dic", "ic_dph")


def matching_subjects(db: Session, payload: SubjectCreate) -> list[Subject]:
    return list(db.query(Subject).filter(or_(*[
        getattr(Subject, field) == getattr(payload, field)
        for field in IDENTIFIERS if getattr(payload, field)
    ])).all())


def same_subject(subject: Subject, payload: SubjectCreate) -> bool:
    return (
        subject.oud == payload.oud
        and " ".join(subject.name.split()).casefold() == " ".join(payload.name.split()).casefold()
        and all(
            not getattr(subject, field) or not getattr(payload, field)
            or getattr(subject, field) == getattr(payload, field)
            for field in IDENTIFIERS
        )
    )
