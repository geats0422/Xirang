"""add review run mode

Revision ID: e7f3c4a2d1b0
Revises: c1e5b2a9f4d1
Create Date: 2026-04-08 15:25:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "e7f3c4a2d1b0"
down_revision = "c1e5b2a9f4d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS runmode")
    op.execute(
        "ALTER TABLE runs ADD CONSTRAINT runmode CHECK (mode IN ('endless', 'speed', 'draft', 'review'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS runmode")
    op.execute(
        "ALTER TABLE runs ADD CONSTRAINT runmode CHECK (mode IN ('endless', 'speed', 'draft'))"
    )
