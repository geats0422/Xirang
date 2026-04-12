from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import UUIDPrimaryKeyMixin


class LearningPath(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_paths"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    path_structure: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow
    )


class LearningPathStage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_stages"
    __table_args__ = (UniqueConstraint("path_id", "stage_index"),)

    path_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    stage_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    best_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
