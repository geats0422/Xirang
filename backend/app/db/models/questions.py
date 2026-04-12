from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"  # Used for Endless Abyss mode


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    question_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("document_question_sets.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text(), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text())
    source_locator: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    question_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )


class QuestionOption(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "question_options"
    __table_args__ = (UniqueConstraint("question_id", "option_key"),)

    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    option_key: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    is_correct: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
