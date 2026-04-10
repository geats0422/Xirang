from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260410_add_updated_at_to_active_effects"
down_revision: str | Sequence[str] | None = "13210a3f6138"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "active_effects",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_column("active_effects", "updated_at")
