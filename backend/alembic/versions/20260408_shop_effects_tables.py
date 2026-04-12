from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260408_shop_effects"
down_revision: str | Sequence[str] | None = "e7f3c4a2d1b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "active_effects",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("effect_type", sa.String(length=40), nullable=False),
        sa.Column("multiplier", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_item_code", sa.String(length=80), nullable=True),
        sa.Column("source_use_id", sa.UUID(), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_active_effects")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_active_effects_user_id")
        ),
    )
    op.create_index(
        "ix_active_effects_user_expires",
        "active_effects",
        ["user_id", "expires_at"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_active_effects_user_type",
        "active_effects",
        ["user_id", "effect_type"],
    )

    op.create_table(
        "use_records",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("item_code", sa.String(length=80), nullable=False),
        sa.Column("inventory_id", sa.UUID(), nullable=True),
        sa.Column("effect_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_use_records")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_use_records_user_id")
        ),
        sa.ForeignKeyConstraint(
            ["inventory_id"],
            ["inventories.id"],
            ondelete="SET NULL",
            name=op.f("fk_use_records_inventory_id"),
        ),
    )
    op.create_index(
        "ix_use_records_user",
        "use_records",
        ["user_id", "used_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("use_records")
    op.drop_table("active_effects")
