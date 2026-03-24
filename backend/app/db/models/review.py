from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class FeedbackType(StrEnum):
    QUESTION_INCORRECT = "question_incorrect"
    QUESTION_UNCLEAR = "question_unclear"
    EXPLANATION_POOR = "explanation_poor"


class FeedbackStatus(StrEnum):
    OPEN = "open"
    SUMMARIZED = "summarized"
    DISMISSED = "dismissed"


class ReviewJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RuleCandidateStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Mistake(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "mistakes"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    explanation: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class MistakeEmbedding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "mistake_embeddings"

    mistake_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mistakes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class QuestionFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "question_feedback"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="SET NULL")
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=FeedbackType.QUESTION_INCORRECT,
        server_default=FeedbackType.QUESTION_INCORRECT.value,
    )
    detail_text: Mapped[str | None] = mapped_column(Text())
    status: Mapped[FeedbackStatus] = mapped_column(
        Enum(
            FeedbackStatus, native_enum=False, create_constraint=True, values_callable=enum_values
        ),
        nullable=False,
        default=FeedbackStatus.OPEN,
        server_default=FeedbackStatus.OPEN.value,
    )


class FeedbackLearningJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback_learning_jobs"

    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[ReviewJobStatus] = mapped_column(
        Enum(
            ReviewJobStatus, native_enum=False, create_constraint=True, values_callable=enum_values
        ),
        nullable=False,
        default=ReviewJobStatus.PENDING,
        server_default=ReviewJobStatus.PENDING.value,
    )
    feedback_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    window_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str | None] = mapped_column(Text())


class ReviewRuleCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_rule_candidates"

    source_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feedback_learning_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[RuleCandidateStatus] = mapped_column(
        Enum(
            RuleCandidateStatus,
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
        ),
        nullable=False,
        default=RuleCandidateStatus.PENDING_REVIEW,
        server_default=RuleCandidateStatus.PENDING_REVIEW.value,
    )


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    entity_table: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_pk: Mapped[str] = mapped_column(String(120), nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
