"""Due-date settings and non-working days (seeded with confirmed days of rest 2026-2028)."""

import sqlalchemy as sa

from alembic import op
from app.due_settings import default_holidays

revision = "0003_due_date_settings"
down_revision = "0002_unique_subjects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "due_date_settings",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("day", sa.Integer()),
        sa.Column("shift_to_workday", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    holidays = op.create_table(
        "public_holidays",
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
    )
    op.bulk_insert(holidays, [
        {"day": day, "name": name}
        for year in (2026, 2027, 2028)
        for day, name in default_holidays(year)
    ])


def downgrade() -> None:
    op.drop_table("public_holidays")
    op.drop_table("due_date_settings")
