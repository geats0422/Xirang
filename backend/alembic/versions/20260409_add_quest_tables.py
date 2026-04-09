"""Add quest_assignments and notifications tables.

Revision ID: 20260409_add_quest_tables
Revises: 20260409_add_active_effects_uq
Create Date: 2026-04-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260409_add_quest_tables"
down_revision: str | Sequence[str] | None = "20260409_add_active_effects_uq"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quest_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quest_code", sa.String(length=60), nullable=False),
        sa.Column(
            "quest_type",
            sa.String(length=20),
            nullable=False,
            server_default="daily",
        ),
        sa.Column("target_metric", sa.String(length=60), nullable=False),
        sa.Column("target_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("progress_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cycle_key", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column(
            "reward_type",
            sa.String(length=20),
            nullable=False,
            server_default="asset",
        ),
        sa.Column("reward_asset_code", sa.String(length=40), nullable=True),
        sa.Column("reward_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_item_code", sa.String(length=80), nullable=True),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "quest_code",
            "cycle_key",
            name="uq_quest_assignments_user_quest_cycle",
        ),
        sa.CheckConstraint(
            "quest_type IN ('daily', 'monthly', 'special')",
            name="ck_quest_type",
        ),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed', 'claimed', 'expired')",
            name="ck_status",
        ),
        sa.CheckConstraint("reward_type IN ('asset', 'item')", name="ck_reward_type"),
    )
    op.create_index(
        "ix_quest_assignments_user_status",
        "quest_assignments",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_quest_assignments_user_cycle",
        "quest_assignments",
        ["user_id", "cycle_key"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("related_quest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id", "is_read"],
        postgresql_where=sa.text("is_read = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_quest_assignments_user_cycle", table_name="quest_assignments")
    op.drop_index("ix_quest_assignments_user_status", table_name="quest_assignments")
    op.drop_table("quest_assignments")
