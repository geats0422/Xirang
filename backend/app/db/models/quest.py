from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import UUIDPrimaryKeyMixin, enum_values


class QuestType(StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"
    SPECIAL = "special"


class QuestStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLAIMED = "claimed"
    EXPIRED = "expired"


class RewardType(StrEnum):
    ASSET = "asset"
    ITEM = "item"


class QuestAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "quest_assignments"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "quest_code", "cycle_key", name="uq_quest_assignments_user_quest_cycle"
        ),
        Index("ix_quest_assignments_user_status", "user_id", "status"),
        Index("ix_quest_assignments_user_cycle", "user_id", "cycle_key"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quest_code: Mapped[str] = mapped_column(String(60), nullable=False)
    quest_type: Mapped[QuestType] = mapped_column(
        Enum(QuestType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=QuestType.DAILY,
        server_default=QuestType.DAILY.value,
    )
    target_metric: Mapped[str] = mapped_column(String(60), nullable=False)
    target_value: Mapped[int] = mapped_column(
        Integer(), nullable=False, default=1, server_default="1"
    )
    progress_value: Mapped[int] = mapped_column(
        Integer(), nullable=False, default=0, server_default="0"
    )
    cycle_key: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[QuestStatus] = mapped_column(
        Enum(QuestStatus, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=QuestStatus.IN_PROGRESS,
        server_default=QuestStatus.IN_PROGRESS.value,
    )
    reward_type: Mapped[RewardType] = mapped_column(
        Enum(RewardType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=RewardType.ASSET,
        server_default=RewardType.ASSET.value,
    )
    reward_asset_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reward_quantity: Mapped[int] = mapped_column(
        Integer(), nullable=False, default=0, server_default="0"
    )
    reward_item_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
