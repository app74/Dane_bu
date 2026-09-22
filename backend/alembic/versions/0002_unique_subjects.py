"""Merge compatible duplicate subjects and enforce unique identifiers."""

import sqlalchemy as sa

from alembic import op

revision = "0002_unique_subjects"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    subjects = sa.Table("subjects", metadata, autoload_with=connection)
    payments = sa.Table("payment_instructions", metadata, autoload_with=connection)
    groups = {}
    for row in connection.execute(sa.select(subjects).order_by(subjects.c.id)).mappings():
        groups.setdefault(row["oud"], []).append(dict(row))
    merges = []
    retained = []
    for rows in groups.values():
        merged = dict(rows[0])
        if len(rows) > 1:
            names = {" ".join(row["name"].split()).casefold() for row in rows}
            if len(names) != 1:
                raise RuntimeError("Duplicitné OÚD má odlišné názvy; vyžaduje ručné posúdenie.")
            for field in ("ico", "dic", "ic_dph"):
                values = {row[field] for row in rows if row[field]}
                if len(values) > 1:
                    raise RuntimeError("Duplicitné OÚD má rozporné identifikátory.")
                merged[field] = next(iter(values), None)
            merges.append((merged, [row["id"] for row in rows[1:]]))
        retained.append(merged)
    for field in ("ico", "dic", "ic_dph"):
        values = [row[field] for row in retained if row[field]]
        if len(values) != len(set(values)):
            raise RuntimeError("Rovnaký identifikátor má odlišné OÚD; vyžaduje ručné posúdenie.")
    for merged, removed_ids in merges:
        connection.execute(subjects.update().where(subjects.c.id == merged["id"]).values(
            **{field: merged[field] for field in ("ico", "dic", "ic_dph")}
        ))
        connection.execute(payments.update().where(payments.c.subject_id.in_(removed_ids)).values(
            subject_id=merged["id"]
        ))
        # Historical JSON snapshots are audit records and deliberately stay unchanged.
        connection.execute(subjects.delete().where(subjects.c.id.in_(removed_ids)))
    for field in ("oud", "ico", "dic", "ic_dph"):
        op.create_index(f"uq_subjects_{field}", "subjects", [field], unique=True)


def downgrade() -> None:
    for field in ("oud", "ico", "dic", "ic_dph"):
        op.drop_index(f"uq_subjects_{field}", table_name="subjects")
