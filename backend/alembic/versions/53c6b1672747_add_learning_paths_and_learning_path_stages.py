"""Add learning_paths and learning_path_stages tables.

Revision ID: 53c6b1672747_add_learning_paths
Revises: 20260409_add_active_effects_uq
Create Date: 2026-04-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "53c6b1672747_add_learning_paths"
down_revision: Union[str, Sequence[str], None] = "20260409_add_active_effects_uq"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("path_structure", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_learning_paths_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_learning_paths_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_learning_paths"),
    )
    op.create_table(
        "learning_path_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_index", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.String(length=20), nullable=False),
        sa.Column("best_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("best_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["path_id"],
            ["learning_paths.id"],
            name="fk_learning_path_stages_path_id_learning_paths",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_learning_path_stages"),
        sa.UniqueConstraint("path_id", "stage_index", name="uq_learning_path_stages_path_id"),
    )


def downgrade() -> None:
    op.drop_table("learning_path_stages")
    op.drop_table("learning_paths")
