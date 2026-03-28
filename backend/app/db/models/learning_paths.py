from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import UUIDPrimaryKeyMixin, enum_values


class LearningPathStatus(StrEnum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class PathTriggerType(StrEnum):
    AUTO_LAZY = "auto_lazy"
    REGENERATE = "regenerate"
    MANUAL_RETRY = "manual_retry"


class LearningPathNodeType(StrEnum):
    SKILL_TREE = "skill_tree"
    UNIT = "unit"
    LEVEL = "level"


class LearningPathProgressStatus(StrEnum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"


class LearningPathVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "mode", "version_no"),
        Index("ix_learning_path_versions_document_mode_created", "document_id", "mode", "created_at"),
        Index("ix_learning_path_versions_status", "status"),
        Index("ix_learning_path_versions_failed_cleanup_at", "failed_cleanup_at"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LearningPathStatus] = mapped_column(
        Enum(LearningPathStatus, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=LearningPathStatus.PENDING,
        server_default=LearningPathStatus.PENDING.value,
    )
    trigger_type: Mapped[PathTriggerType] = mapped_column(
        Enum(PathTriggerType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=PathTriggerType.AUTO_LAZY,
        server_default=PathTriggerType.AUTO_LAZY.value,
    )
    generator_config_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    source_content_hash: Mapped[str | None] = mapped_column(String(64))
    generation_job_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL")
    )
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_cleanup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LearningPathNode(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_nodes"
    __table_args__ = (
        UniqueConstraint("path_version_id", "node_key"),
        Index("ix_learning_path_nodes_parent_sort", "parent_node_id", "sort_order"),
    )

    path_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("learning_path_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_type: Mapped[LearningPathNodeType] = mapped_column(
        Enum(LearningPathNodeType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
    )
    node_key: Mapped[str] = mapped_column(String(120), nullable=False)
    parent_node_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_path_nodes.id", ondelete="CASCADE")
    )
    is_mode_branch: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unlock_rule_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    question_selector_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    meta_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class LearningPathProgress(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "path_version_id", "node_id"),
        Index("ix_learning_path_progress_user_path", "user_id", "path_version_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    path_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_path_versions.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_path_nodes.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[LearningPathProgressStatus] = mapped_column(
        Enum(LearningPathProgressStatus, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=LearningPathProgressStatus.LOCKED,
        server_default=LearningPathProgressStatus.LOCKED.value,
    )
    first_completed_run_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="SET NULL")
    )
    completed_runs_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )


class LegendReviewProgress(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "legend_review_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "path_version_id", "unit_node_id"),
        Index("ix_legend_review_progress_user_path", "user_id", "path_version_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    path_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_path_versions.id", ondelete="CASCADE"), nullable=False
    )
    unit_node_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_path_nodes.id", ondelete="CASCADE"), nullable=False
    )
    legend_round_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_legend_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )


class PathRegenerationRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "path_regeneration_records"
    __table_args__ = (
        Index("ix_path_regeneration_records_doc_mode_created", "document_id", "mode", "created_at"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    path_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_path_versions.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
