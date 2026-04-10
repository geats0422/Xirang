"""Fix runs.mode constraint to include review mode.

Revision ID: 20260410b901
Revises: 20260410ae01
Create Date: 2026-04-10
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260410b901"
down_revision: str | Sequence[str] | None = "20260410ae01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS ck_runs_runmode")
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS runmode")
    op.execute(
        "ALTER TABLE runs ADD CONSTRAINT ck_runs_runmode "
        "CHECK (mode IN ('endless', 'speed', 'draft', 'review'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS ck_runs_runmode")
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS runmode")
    op.execute(
        "ALTER TABLE runs ADD CONSTRAINT ck_runs_runmode "
        "CHECK (mode IN ('endless', 'speed', 'draft'))"
    )
