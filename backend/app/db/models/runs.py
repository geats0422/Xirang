from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
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


class RunMode(StrEnum):
    ENDLESS = "endless"
    SPEED = "speed"
    DRAFT = "draft"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"


class Run(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "runs"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL")
    )
    source_question_set_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("document_question_sets.id", ondelete="SET NULL"),
    )
    mode: Mapped[RunMode] = mapped_column(
        Enum(RunMode, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=RunStatus.RUNNING,
        server_default=RunStatus.RUNNING.value,
    )
    score: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    correct_answers: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    combo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunQuestion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "run_questions"
    __table_args__ = (UniqueConstraint("run_id", "sequence_no"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_reason: Mapped[str | None] = mapped_column(String(120))
    prompt_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB)


class RunAnswer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "run_answers"
    __table_args__ = (UniqueConstraint("run_question_id"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    run_question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("run_questions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    free_text_answer: Mapped[str | None] = mapped_column(Text())
    is_correct: Mapped[bool | None] = mapped_column()
    answer_time_ms: Mapped[int | None] = mapped_column(Integer)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Settlement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "settlements"
    __table_args__ = (UniqueConstraint("run_id"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    xp_gained: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    coin_reward: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    combo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    accuracy_pct: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0, server_default="0"
    )
    rule_version: Mapped[str] = mapped_column(
        String(40), nullable=False, default="v1", server_default="v1"
    )
    payload: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    settled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class SeasonStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"


class Season(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "seasons"

    season_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SeasonStatus] = mapped_column(
        Enum(SeasonStatus, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=SeasonStatus.PENDING,
        server_default=SeasonStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
