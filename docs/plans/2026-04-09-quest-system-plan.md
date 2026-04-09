# 任务系统（Quest System）实现计划

**Goal:** 实现后端任务系统和消息通知系统，前端对接真实 API，支持每日任务自动重置、进度同步、奖励领取、通知展示。

**Architecture:** 
- 后端：FastAPI + SQLAlchemy 2.0 async + PostgreSQL
- 前端：Vue 3 + TypeScript + Vite + vue-i18n
- 奖励发放复用现有 wallet_ledger 和 inventories 表

**Tech Stack:** 
- Backend: FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic
- Frontend: Vue 3, vue-i18n, @vue/test-utils, Vitest

**Design Spec:** docs/specs/2026-04-09-quest-system-design.md

---

## 任务列表

### Task 1: 创建数据库迁移文件

**Files:**
- Create: `backend/alembic/versions/xxxx_add_quest_tables.py`

```python
"""Add quest_assignments and notifications tables.

Revision ID: xxxx_add_quest_tables
Revises: 5f1feb885f66
Create Date: 2026-04-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "xxxx_add_quest_tables"
down_revision: Union[str, Sequence[str], None] = "5f1feb885f66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # quest_assignments table
    op.create_table(
        "quest_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_code", sa.String(length=60), nullable=False),
        sa.Column("quest_type", sa.String(length=20), nullable=False, server_default="daily"),
        sa.Column("target_metric", sa.String(length=60), nullable=False),
        sa.Column("target_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("progress_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cycle_key", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.Column("reward_type", sa.String(length=20), nullable=False, server_default="asset"),
        sa.Column("reward_asset_code", sa.String(length=40), nullable=True),
        sa.Column("reward_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_item_code", sa.String(length=80), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "quest_code", "cycle_key", name="uq_quest_assignments_user_quest_cycle"),
        sa.CheckConstraint("quest_type IN ('daily', 'monthly', 'special')", name="ck_quest_type"),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'claimed', 'expired')", name="ck_status"),
        sa.CheckConstraint("reward_type IN ('asset', 'item')", name="ck_reward_type"),
    )
    op.create_index("ix_quest_assignments_user_status", "quest_assignments", ["user_id", "status"])
    op.create_index("ix_quest_assignments_user_cycle", "quest_assignments", ["user_id", "cycle_key"])

    # notifications table
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("related_quest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"], postgresql_where=sa.text("is_read = false"))


def downgrade() -> None:
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_quest_assignments_user_cycle", table_name="quest_assignments")
    op.drop_index("ix_quest_assignments_user_status", table_name="quest_assignments")
    op.drop_table("quest_assignments")
```

- [ ] **Step 1: Run migration to verify**

Run: `cd backend && uv run alembic upgrade head`
Expected: SUCCESS

- [ ] **Step 2: Commit**

```bash
git add backend/alembic/versions/xxxx_add_quest_tables.py
git commit -m "feat: add quest_assignments and notifications tables"
```

---

### Task 2: 创建后端 QuestAssignment 模型

**Files:**
- Create: `backend/app/db/models/quest.py`
- Modify: `backend/app/db/models/__init__.py:31` (add export)

```python
"""Quest assignment models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_values


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
        UniqueConstraint("user_id", "quest_code", "cycle_key", name="uq_quest_assignments_user_quest_cycle"),
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
    target_value: Mapped[int] = mapped_column(Integer(), nullable=False, default=1, server_default="1")
    progress_value: Mapped[int] = mapped_column(Integer(), nullable=False, default=0, server_default="0")
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
    reward_quantity: Mapped[int] = mapped_column(Integer(), nullable=False, default=0, server_default="0")
    reward_item_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 1: Run mypy to verify**

Run: `cd backend && uv run mypy app/db/models/quest.py`
Expected: PASS (no errors)

- [ ] **Step 2: Commit**

```bash
git add backend/app/db/models/quest.py backend/app/db/models/__init__.py
git commit -m "feat: add QuestAssignment model"
```

---

### Task 3: 创建后端 Notification 模型

**Files:**
- Create: `backend/app/db/models/notification.py`
- Modify: `backend/app/db/models/__init__.py` (add export)

```python
"""Notification models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read", postgresql_where="is_read = false"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_read: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    related_quest_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 1: Run mypy to verify**

Run: `cd backend && uv run mypy app/db/models/notification.py`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add backend/app/db/models/notification.py backend/app/db/models/__init__.py
git commit -m "feat: add Notification model"
```

---

### Task 4: 创建后端 Quest Schemas

**Files:**
- Create: `backend/app/services/quest/schemas.py`

```python
"""Quest service schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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


class ActionType(StrEnum):
    CLAIM = "claim"
    NAVIGATE = "navigate"
    CONTINUE = "continue"


class IconTone(StrEnum):
    VIOLET = "violet"
    GREEN = "green"
    BLUE = "blue"
    AMBER = "amber"


class QuestAssignmentResponse(BaseModel):
    id: UUID
    quest_code: str
    quest_type: Literal["daily", "monthly", "special"]
    title_i18n_key: str
    description_i18n_key: str
    target_metric: str
    target_value: int
    progress_value: int
    status: Literal["in_progress", "completed", "claimed", "expired"]
    reward_type: Literal["asset", "item"]
    reward_asset_code: str | None
    reward_quantity: int
    reward_item_code: str | None
    reward_i18n_key: str
    reward_icon: str
    action_i18n_key: str
    action_type: Literal["claim", "navigate", "continue"]
    navigate_to: str | None
    icon: str
    icon_tone: Literal["violet", "green", "blue", "amber"]
    expires_at: datetime | None
    locked: bool

    model_config = {"from_attributes": True}


class MonthlyProgressResponse(BaseModel):
    current: int
    target: int
    year_month: str
    days_remaining: int
    completed_day_keys: list[str]


class QuestListResponse(BaseModel):
    daily_quests: list[QuestAssignmentResponse]
    daily_refresh_at: datetime
    monthly_progress: MonthlyProgressResponse
    streak_days: int
    streak_milestone: dict | None


class QuestClaimResponse(BaseModel):
    assignment_id: UUID
    status: Literal["claimed"]
    reward_type: str
    reward_asset_code: str | None
    reward_quantity: int
    reward_item_code: str | None
    coin_balance_after: int | None
    item_quantity_after: int | None
```

- [ ] **Step 1: Run ruff check**

Run: `cd backend && uv run ruff check app/services/quest/schemas.py`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/quest/schemas.py
git commit -m "feat: add quest service schemas"
```

---

### Task 5: 创建后端 Quest Repository

**Files:**
- Create: `backend/app/repositories/quest_repository.py`

```python
"""Quest repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.quest import QuestAssignment, QuestStatus

if TYPE_CHECKING:
    pass


class QuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_quests_by_cycle(
        self, user_id: UUID, cycle_key: str
    ) -> list[QuestAssignment]:
        stmt = select(QuestAssignment).where(
            and_(
                QuestAssignment.user_id == user_id,
                QuestAssignment.cycle_key == cycle_key,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_quest(
        self, user_id: UUID, quest_code: str, cycle_key: str
    ) -> QuestAssignment | None:
        stmt = select(QuestAssignment).where(
            and_(
                QuestAssignment.user_id == user_id,
                QuestAssignment.quest_code == quest_code,
                QuestAssignment.cycle_key == cycle_key,
            )
        ).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quest_by_id(
        self, assignment_id: UUID
    ) -> QuestAssignment | None:
        stmt = select(QuestAssignment).where(
            QuestAssignment.id == assignment_id
        ).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_quest(
        self,
        *,
        user_id: UUID,
        quest_code: str,
        quest_type: str,
        target_metric: str,
        target_value: int,
        cycle_key: str,
        reward_type: str,
        reward_asset_code: str | None = None,
        reward_quantity: int = 0,
        reward_item_code: str | None = None,
        expires_at: datetime | None = None,
    ) -> QuestAssignment:
        quest = QuestAssignment(
            user_id=user_id,
            quest_code=quest_code,
            quest_type=quest_type,
            target_metric=target_metric,
            target_value=target_value,
            cycle_key=cycle_key,
            reward_type=reward_type,
            reward_asset_code=reward_asset_code,
            reward_quantity=reward_quantity,
            reward_item_code=reward_item_code,
            expires_at=expires_at,
            assigned_at=datetime.now(UTC),
        )
        self._session.add(quest)
        await self._session.flush()
        return quest

    async def update_progress(
        self,
        assignment_id: UUID,
        progress_value: int,
        status: QuestStatus | None = None,
    ) -> QuestAssignment | None:
        quest = await self.get_quest_by_id(assignment_id)
        if quest is None:
            return None
        quest.progress_value = progress_value
        if status:
            quest.status = status
            if status == QuestStatus.COMPLETED:
                quest.completed_at = datetime.now(UTC)
        await self._session.flush()
        return quest

    async def mark_claimed(self, assignment_id: UUID) -> QuestAssignment | None:
        quest = await self.get_quest_by_id(assignment_id)
        if quest is None:
            return None
        quest.status = QuestStatus.CLAIMED
        quest.claimed_at = datetime.now(UTC)
        await self._session.flush()
        return quest

    async def mark_expired(self, assignment_id: UUID) -> QuestAssignment | None:
        quest = await self.get_quest_by_id(assignment_id)
        if quest is None:
            return None
        quest.status = QuestStatus.EXPIRED
        await self._session.flush()
        return quest

    async def count_monthly_completed(
        self, user_id: UUID, year_month: str
    ) -> int:
        stmt = select(func.count(QuestAssignment.id)).where(
            and_(
                QuestAssignment.user_id == user_id,
                QuestAssignment.cycle_key.startswith(year_month),
                QuestAssignment.status.in_([QuestStatus.COMPLETED, QuestStatus.CLAIMED]),
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_monthly_completed_days(
        self, user_id: UUID, year_month: str
    ) -> list[str]:
        stmt = (
            select(QuestAssignment.cycle_key)
            .where(
                and_(
                    QuestAssignment.user_id == user_id,
                    QuestAssignment.cycle_key.startswith(year_month),
                    QuestAssignment.status.in_([QuestStatus.COMPLETED, QuestStatus.CLAIMED]),
                    QuestAssignment.quest_type == "daily",
                )
            )
            .distinct()
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

- [ ] **Step 1: Run ruff check**

Run: `cd backend && uv run ruff check app/repositories/quest_repository.py`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add backend/app/repositories/quest_repository.py
git commit -m "feat: add quest repository"
```

---

### Task 6: 创建后端 Quest Service

**Files:**
- Create: `backend/app/services/quest/service.py`

```python
"""Quest service with business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.repositories.quest_repository import QuestRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.quest.schemas import (
    ActionType,
    IconTone,
    MonthlyProgressResponse,
    QuestAssignmentResponse,
    QuestClaimResponse,
    QuestListResponse,
    QuestType,
)
from app.services.notification.service import NotificationService

if TYPE_CHECKING:
    pass


QUEST_DEFINITIONS = {
    "quest-upload": {
        "title_i18n_key": "quests.missionUploadTitle",
        "target_metric": "document_upload",
        "target_value": 1,
        "reward_type": "item",
        "reward_item_code": "gold_chest",
        "reward_i18n_key": "quests.rewardGoldChest",
        "reward_icon": "🧰",
        "icon": "📤",
        "icon_tone": "violet",
        "action_type": ActionType.NAVIGATE,
        "navigate_to": "/library?action=upload",
    },
    "quest-streak": {
        "title_i18n_key": "quests.missionStreakTitle",
        "target_metric": "streak",
        "target_value": 1,
        "reward_type": "asset",
        "reward_asset_code": "COIN",
        "reward_quantity": 50,
        "reward_i18n_key": "quests.rewardCoins50",
        "reward_icon": "🪙",
        "icon": "🔥",
        "icon_tone": "amber",
        "action_type": ActionType.CONTINUE,
        "navigate_to": None,
    },
}


class QuestServiceError(Exception):
    pass


class QuestNotFoundError(QuestServiceError):
    pass


class QuestNotCompletedError(QuestServiceError):
    pass


class QuestAlreadyClaimedError(QuestServiceError):
    pass


class QuestExpiredError(QuestServiceError):
    pass


class QuestService:
    def __init__(
        self,
        quest_repository: QuestRepository,
        wallet_repository: WalletRepository,
        notification_service: NotificationService,
    ) -> None:
        self._quest_repo = quest_repository
        self._wallet_repo = wallet_repository
        self._notification_service = notification_service

    def _get_today_cycle_key(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _get_month_cycle_key(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m")

    def _get_monthly_progress(self, user_id: UUID) -> MonthlyProgressResponse:
        year_month = self._get_month_cycle_key()
        now = datetime.now(UTC)
        total_days = (datetime(now.year, now.month + 1, 1) - datetime(now.year, now.month, 1)).days if now.month < 12 else 31
        days_remaining = total_days - now.day
        current = 0  # Will be fetched from DB

        return MonthlyProgressResponse(
            current=current,
            target=30,
            year_month=year_month,
            days_remaining=days_remaining,
            completed_day_keys=[],
        )

    async def get_user_quests(self, user_id: UUID) -> QuestListResponse:
        today_key = self._get_today_cycle_key()
        quests = await self._quest_repo.get_user_quests_by_cycle(user_id, today_key)

        if not quests:
            quests = await self._ensure_daily_quests(user_id, today_key)

        quest_responses = []
        for q in quests:
            definition = QUEST_DEFINITIONS.get(q.quest_code, {})
            quest_responses.append(
                QuestAssignmentResponse(
                    id=q.id,
                    quest_code=q.quest_code,
                    quest_type=q.quest_type,
                    title_i18n_key=definition.get("title_i18n_key", f"quests.{q.quest_code}Title"),
                    description_i18n_key=definition.get("description_i18n_key", ""),
                    target_metric=q.target_metric,
                    target_value=q.target_value,
                    progress_value=q.progress_value,
                    status=q.status,
                    reward_type=q.reward_type,
                    reward_asset_code=q.reward_asset_code,
                    reward_quantity=q.reward_quantity,
                    reward_item_code=q.reward_item_code,
                    reward_i18n_key=definition.get("reward_i18n_key", ""),
                    reward_icon=definition.get("reward_icon", "🎁"),
                    action_i18n_key="quests.claimReward" if q.status == "completed" else ("quests.upload" if definition.get("action_type") == ActionType.NAVIGATE else "quests.continue"),
                    action_type=definition.get("action_type", ActionType.CONTINUE),
                    navigate_to=definition.get("navigate_to"),
                    icon=definition.get("icon", "✦"),
                    icon_tone=definition.get("icon_tone", IconTone.BLUE),
                    expires_at=q.expires_at,
                    locked=False,
                )
            )

        monthly_progress = self._get_monthly_progress(user_id)

        return QuestListResponse(
            daily_quests=quest_responses,
            daily_refresh_at=datetime(now.year, now.month, now.day, 23, 59, 59),
            monthly_progress=monthly_progress,
            streak_days=0,
            streak_milestone=None,
        )

    async def _ensure_daily_quests(self, user_id: UUID, cycle_key: str) -> list:
        quests = []
        for quest_code, definition in QUEST_DEFINITIONS.items():
            existing = await self._quest_repo.get_user_quest(user_id, quest_code, cycle_key)
            if not existing:
                expires_at = datetime.strptime(cycle_key + " 23:59:59", "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
                quest = await self._quest_repo.create_quest(
                    user_id=user_id,
                    quest_code=quest_code,
                    quest_type=QuestType.DAILY,
                    target_metric=definition["target_metric"],
                    target_value=definition["target_value"],
                    cycle_key=cycle_key,
                    reward_type=definition["reward_type"],
                    reward_asset_code=definition.get("reward_asset_code"),
                    reward_quantity=definition.get("reward_quantity", 0),
                    reward_item_code=definition.get("reward_item_code"),
                    expires_at=expires_at,
                )
                quests.append(quest)
            else:
                quests.append(existing)
        await self._quest_repo.commit()
        return quests

    async def claim_reward(
        self, user_id: UUID, assignment_id: UUID
    ) -> QuestClaimResponse:
        quest = await self._quest_repo.get_quest_by_id(assignment_id)
        if quest is None:
            raise QuestNotFoundError(f"Quest {assignment_id} not found")

        if quest.user_id != user_id:
            raise QuestNotFoundError(f"Quest {assignment_id} not found")

        if quest.status == "claimed":
            raise QuestAlreadyClaimedError("Quest already claimed")

        if quest.status == "expired":
            raise QuestExpiredError("Quest has expired")

        if quest.status != "completed":
            raise QuestNotCompletedError("Quest not yet completed")

        await self._quest_repo.mark_claimed(assignment_id)

        coin_balance = None
        item_quantity = None

        if quest.reward_type == "asset" and quest.reward_asset_code:
            await self._wallet_repo.create_ledger_entry(
                user_id=user_id,
                asset_code=quest.reward_asset_code,
                delta=quest.reward_quantity,
                reason_code="quest_claim",
                source_type="quest",
                source_id=assignment_id,
            )
            coin_balance = await self._wallet_repo.get_balance(user_id, quest.reward_asset_code)

        elif quest.reward_type == "item" and quest.reward_item_code:
            item_quantity = 1

        await self._notification_service.create_notification(
            user_id=user_id,
            type="quest_claimed",
            title="奖励已领取" if False else "Reward claimed",
            body=None,
            related_quest_id=assignment_id,
        )

        await self._quest_repo.commit()

        return QuestClaimResponse(
            assignment_id=assignment_id,
            status="claimed",
            reward_type=quest.reward_type,
            reward_asset_code=quest.reward_asset_code,
            reward_quantity=quest.reward_quantity,
            reward_item_code=quest.reward_item_code,
            coin_balance_after=coin_balance,
            item_quantity_after=item_quantity,
        )
```

- [ ] **Step 1: Run ruff check**

Run: `cd backend && uv run ruff check app/services/quest/service.py`
Expected: PASS

- [ ] **Step 2: Run mypy**

Run: `cd backend && uv run mypy app/services/quest/service.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/quest/service.py
git commit -m "feat: add quest service with business logic"
```

---

### Task 7: 创建后端 Notification Repository 和 Service

**Files:**
- Create: `backend/app/repositories/notification_repository.py`
- Create: `backend/app/services/notification/schemas.py`
- Create: `backend/app/services/notification/service.py`

```python
# backend/app/repositories/notification_repository.py
"""Notification repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification

if TYPE_CHECKING:
    pass


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_notifications(
        self, user_id: UUID, limit: int = 50
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        stmt = select(Notification).where(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        )
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))

    async def mark_read(self, notification_id: UUID) -> Notification | None:
        stmt = select(Notification).where(Notification.id == notification_id).limit(1)
        result = await self._session.execute(stmt)
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self._session.flush()
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def create_notification(
        self,
        *,
        user_id: UUID,
        type: str,
        title: str,
        body: str | None = None,
        related_quest_id: UUID | None = None,
        action_url: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            related_quest_id=related_quest_id,
            action_url=action_url,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

```python
# backend/app/services/notification/schemas.py
"""Notification service schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str | None
    is_read: bool
    related_quest_id: UUID | None
    action_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
```

```python
# backend/app/services/notification/service.py
"""Notification service."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.repositories.notification_repository import NotificationRepository
from app.services.notification.schemas import (
    NotificationListResponse,
    NotificationResponse,
)

if TYPE_CHECKING:
    pass


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self._repo = repository

    async def get_user_notifications(
        self, user_id: UUID
    ) -> NotificationListResponse:
        notifications = await self._repo.get_user_notifications(user_id)
        unread_count = await self._repo.get_unread_count(user_id)

        return NotificationListResponse(
            items=[
                NotificationResponse.model_validate(n) for n in notifications
            ],
            unread_count=unread_count,
        )

    async def mark_read(self, notification_id: UUID) -> NotificationResponse | None:
        notification = await self._repo.mark_read(notification_id)
        if notification:
            return NotificationResponse.model_validate(notification)
        return None

    async def mark_all_read(self, user_id: UUID) -> int:
        return await self._repo.mark_all_read(user_id)

    async def create_notification(
        self,
        *,
        user_id: UUID,
        type: str,
        title: str,
        body: str | None = None,
        related_quest_id: UUID | None = None,
        action_url: str | None = None,
    ) -> NotificationResponse:
        notification = await self._repo.create_notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            related_quest_id=related_quest_id,
            action_url=action_url,
        )
        await self._repo.commit()
        return NotificationResponse.model_validate(notification)
```

- [ ] **Step 1: Run ruff check all files**

Run: `cd backend && uv run ruff check app/repositories/notification_repository.py app/services/notification/`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add backend/app/repositories/notification_repository.py backend/app/services/notification/
git commit -m "feat: add notification repository and service"
```

---

### Task 8: 创建后端 API 路由

**Files:**
- Create: `backend/app/api/v1/quests.py`
- Create: `backend/app/api/v1/notifications.py`
- Modify: `backend/app/api/router.py` (add imports and register routers)

```python
# backend/app/api/v1/quests.py
"""Quest API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.notification_repository import NotificationRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.quest import QuestClaimResponse, QuestListResponse
from app.services.notification.service import NotificationService
from app.services.quest.service import (
    QuestAlreadyClaimedError,
    QuestExpiredError,
    QuestNotCompletedError,
    QuestNotFoundError,
    QuestService,
)

router = APIRouter(prefix="/quests", tags=["quests"])


async def get_quest_repository(session: AsyncSession = Depends(get_db_session)) -> QuestRepository:
    return QuestRepository(session)


async def get_notification_repository(session: AsyncSession = Depends(get_db_session)) -> NotificationRepository:
    return NotificationRepository(session)


async def get_wallet_repository(session: AsyncSession = Depends(get_db_session)) -> WalletRepository:
    return WalletRepository(session)


def get_quest_service(
    quest_repo: QuestRepository = Depends(get_quest_repository),
    wallet_repo: WalletRepository = Depends(get_wallet_repository),
    notification_repo: NotificationRepository = Depends(get_notification_repository),
) -> QuestService:
    return QuestService(
        quest_repository=quest_repo,
        wallet_repository=wallet_repo,
        notification_service=NotificationService(notification_repo),
    )


@router.get("", response_model=QuestListResponse)
async def get_quests(
    user_id: UUID = Depends(get_current_user_id),
    service: QuestService = Depends(get_quest_service),
) -> QuestListResponse:
    return await service.get_user_quests(user_id)


@router.post("/{assignment_id}/claim", response_model=QuestClaimResponse)
async def claim_quest_reward(
    assignment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: QuestService = Depends(get_quest_service),
) -> QuestClaimResponse:
    try:
        return await service.claim_reward(user_id, assignment_id)
    except QuestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except QuestNotCompletedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except QuestAlreadyClaimedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except QuestExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e)) from e
```

```python
# backend/app/api/v1/notifications.py
"""Notification API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.notification_repository import NotificationRepository
from app.services.notification.schemas import NotificationListResponse, NotificationResponse
from app.services.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return NotificationRepository(session)


def get_notification_service(
    repo: NotificationRepository = Depends(get_notification_repository),
) -> NotificationService:
    return NotificationService(repo)


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    return await service.get_user_notifications(user_id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse | None)
async def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse | None:
    return await service.mark_read(notification_id)


@router.post("/read-all")
async def mark_all_notifications_read(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    updated_count = await service.mark_all_read(user_id)
    return {"updated_count": updated_count}
```

- [ ] **Step 1: Run ruff check**

Run: `cd backend && uv run ruff check app/api/v1/quests.py app/api/v1/notifications.py`
Expected: PASS

- [ ] **Step 2: Run mypy**

Run: `cd backend && uv run mypy app/api/v1/quests.py app/api/v1/notifications.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/quests.py backend/app/api/v1/notifications.py backend/app/api/router.py
git commit -m "feat: add quests and notifications API routes"
```

---

### Task 9: 创建前端 API 调用

**Files:**
- Create: `frontend/src/api/quests.ts`
- Create: `frontend/src/api/notifications.ts`

```typescript
// frontend/src/api/quests.ts
import { http } from "./http";
import type { QuestListResponse, QuestClaimResponse, MonthlyProgressResponse } from "./types";

export interface QuestAssignmentResponse {
  id: string;
  quest_code: string;
  quest_type: "daily" | "monthly" | "special";
  title_i18n_key: string;
  description_i18n_key: string;
  target_metric: string;
  target_value: number;
  progress_value: number;
  status: "in_progress" | "completed" | "claimed" | "expired";
  reward_type: "asset" | "item";
  reward_asset_code: string | null;
  reward_quantity: number;
  reward_item_code: string | null;
  reward_i18n_key: string;
  reward_icon: string;
  action_i18n_key: string;
  action_type: "claim" | "navigate" | "continue";
  navigate_to: string | null;
  icon: string;
  icon_tone: "violet" | "green" | "blue" | "amber";
  expires_at: string | null;
  locked: boolean;
}

export interface MonthlyProgressResponse {
  current: number;
  target: number;
  year_month: string;
  days_remaining: number;
  completed_day_keys: string[];
}

export interface QuestListResponse {
  daily_quests: QuestAssignmentResponse[];
  daily_refresh_at: string;
  monthly_progress: MonthlyProgressResponse;
  streak_days: number;
  streak_milestone: Record<string, unknown> | null;
}

export interface QuestClaimResponse {
  assignment_id: string;
  status: "claimed";
  reward_type: string;
  reward_asset_code: string | null;
  reward_quantity: number;
  reward_item_code: string | null;
  coin_balance_after: number | null;
  item_quantity_after: number | null;
}

export async function getQuests(): Promise<QuestListResponse> {
  return http.get<QuestListResponse>("/quests");
}

export async function claimQuestReward(assignmentId: string): Promise<QuestClaimResponse> {
  return http.post<QuestClaimResponse>(`/quests/${assignmentId}/claim`);
}

export async function getMonthlyProgress(): Promise<MonthlyProgressResponse> {
  return http.get<MonthlyProgressResponse>("/quests/monthly-progress");
}
```

```typescript
// frontend/src/api/notifications.ts
import { http } from "./http";

export interface NotificationResponse {
  id: string;
  type: string;
  title: string;
  body: string | null;
  is_read: boolean;
  related_quest_id: string | null;
  action_url: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationResponse[];
  unread_count: number;
}

export async function getNotifications(): Promise<NotificationListResponse> {
  return http.get<NotificationListResponse>("/notifications");
}

export async function markNotificationRead(notificationId: string): Promise<NotificationResponse | null> {
  return http.patch<NotificationResponse | null>(`/notifications/${notificationId}/read`);
}

export async function markAllNotificationsRead(): Promise<{ updated_count: number }> {
  return http.post<{ updated_count: number }>("/notifications/read-all");
}
```

- [ ] **Step 1: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/quests.ts frontend/src/api/notifications.ts
git commit -m "feat: add quests and notifications API clients"
```

---

### Task 10: 创建前端工具函数

**Files:**
- Create: `frontend/src/utils/questUtils.ts`

```typescript
// frontend/src/utils/questUtils.ts

export function getDaysRemainingInMonth(): number {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();
  const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
  return totalDaysInMonth - today;
}

export function formatRefreshTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  if (diffMs <= 0) return "0小时";
  const hours = Math.ceil(diffMs / (1000 * 60 * 60));
  return `${hours}小时`;
}

export function getNotificationTimeAgo(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const minutes = Math.floor(diffMs / (1000 * 60));
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  return `${days}天前`;
}
```

- [ ] **Step 1: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add frontend/src/utils/questUtils.ts
git commit -m "feat: add quest utility functions"
```

---

### Task 11: 更新前端 i18n 翻译

**Files:**
- Modify: `frontend/src/i18n/index.ts` (add new translation keys)

在 `zh-CN` 和 `en` 的 `quests` 部分添加以下新 keys：

```typescript
// zh-CN quests 部分新增
missionAccuracyTitle: "单次答题正确率达到 80%",
missionTimeTitle: "学习时长达到 10 分钟",
missionFloorsTitle: "在「无尽深渊」到达第 5 层",
missionSpeedTitle: "在「极速生存」完成 1 局挑战",
missionDraftTitle: "在「知识牌局」完成 1 局挑战",
missionAbyssDeepTitle: "在「无尽深渊」到达第 10 层",
missionStreak7Title: "连续打卡 7 天",
missionStreak15Title: "连续打卡 15 天",
missionStreak30Title: "连续打卡 30 天",
rewardTimeTreasure10: "时间宝·刻（延长翻倍 10 分钟）",
rewardTimeTreasure15: "时间宝·时（延长翻倍 15 分钟）",
rewardTimeTreasure30: "时间宝·日（延长翻倍 30 分钟）",
rewardCoins30: "+30 金币",
rewardCoins20: "+20 金币",
rewardCoins25: "+25 金币",
rewardCoins50: "+50 金币",
rewardCoins100: "+100 金币",
rewardCoins200: "+200 金币",
rewardCoins500: "+500 金币",
claimSuccess: "奖励已领取！",
claimFailed: "领取失败，请稍后重试",
questExpired: "任务已过期",
questNotCompleted: "任务尚未完成",
questNotFound: "任务不存在",
daysRemainingShort: "⏰ 剩余 {days} 天",
monthlyBadgeDesc: "完成 30 个每日任务即可获得月度徽章",
streakMilestone7: "连胜 7 天达成！",
streakMilestone15: "连胜 15 天达成！获得时间宝·日",
streakMilestone30: "连胜 30 天达成！获得双倍时间宝",
notificationQuestReward: "任务奖励可领取",
notificationClaimed: "奖励已领取",
notificationStreakWarning: "连胜即将中断！",
notificationQuestExpiring: "每日任务即将过期",
notificationMonthlyProgress: "月度进度 {current}/30",
notificationTimeTreasure: "获得时间宝！",

// en quests 部分新增
missionAccuracyTitle: "Achieve 80%+ accuracy in a single run",
missionTimeTitle: "Study for 10 minutes",
missionFloorsTitle: "Reach floor 5 in Endless Abyss",
missionSpeedTitle: "Complete 1 run in Speed Survival",
missionDraftTitle: "Complete 1 run in Knowledge Draft",
missionAbyssDeepTitle: "Reach floor 10 in Endless Abyss",
missionStreak7Title: "7-day streak",
missionStreak15Title: "15-day streak",
missionStreak30Title: "30-day streak",
rewardTimeTreasure10: "Time Treasure·Quarter (extends boost 10 min)",
rewardTimeTreasure15: "Time Treasure·Hourglass (extends boost 15 min)",
rewardTimeTreasure30: "Time Treasure·Sundial (extends boost 30 min)",
rewardCoins30: "+30 Coins",
rewardCoins20: "+20 Coins",
rewardCoins25: "+25 Coins",
rewardCoins50: "+50 Coins",
rewardCoins100: "+100 Coins",
rewardCoins200: "+200 Coins",
rewardCoins500: "+500 Coins",
claimSuccess: "Reward claimed!",
claimFailed: "Failed to claim. Please try again later.",
questExpired: "Quest has expired",
questNotCompleted: "Quest not yet completed",
questNotFound: "Quest not found",
daysRemainingShort: "⏰ {days} days remaining",
monthlyBadgeDesc: "Complete 30 daily quests to earn the monthly badge",
streakMilestone7: "7-day streak achieved!",
streakMilestone15: "15-day streak achieved! Time Treasure·Sundial earned!",
streakMilestone30: "30-day streak achieved! Double Time Treasure earned!",
notificationQuestReward: "Quest reward available",
notificationClaimed: "Reward claimed",
notificationStreakWarning: "Your streak is about to break!",
notificationQuestExpiring: "Daily quests expiring soon",
notificationMonthlyProgress: "Monthly progress {current}/30",
notificationTimeTreasure: "Time Treasure acquired!",
```

- [ ] **Step 1: Run lint**

Run: `cd frontend && npm run lint`
Expected: PASS (max-warnings=0)

- [ ] **Step 2: Commit**

```bash
git add frontend/src/i18n/index.ts
git commit -m "feat: add quest and notification i18n translations"
```

---

### Task 12: 更新前端 QuestsPage 组件

**Files:**
- Modify: `frontend/src/pages/DungeonScholarQuestsPage.vue`

主要改动：
1. 替换 localStorage 数据获取为 `getQuests()` API 调用
2. 替换硬编码 notifications 为 `getNotifications()` API 调用
3. 小圆点显示逻辑改为 `unreadCount > 0`
4. 领取奖励按钮添加 `claimQuestReward()` API 调用
5. 修复月度进度剩余天数计算

- [ ] **Step 1: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 2: Run test**

Run: `cd frontend && npm run test -- --testPathPattern=DungeonScholarQuestsPage.spec.ts`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DungeonScholarQuestsPage.vue
git commit -m "feat: connect QuestsPage to backend API"
```

---

### Task 13: 更新前端 NotificationPopover 组件

**Files:**
- Modify: `frontend/src/components/NotificationPopover.vue`

主要改动：
1. 替换硬编码 notifications 为 props 或 API 调用
2. 添加点击标记已读逻辑

- [ ] **Step 1: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 2: Run test**

Run: `cd frontend && npm run test -- --testPathPattern=NotificationPopover.spec.ts`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/NotificationPopover.vue
git commit -m "feat: connect NotificationPopover to backend API"
```

---

### Task 14: 编写后端 API 测试

**Files:**
- Create: `backend/tests/api/test_quests_api.py`
- Create: `backend/tests/api/test_notifications_api.py`

- [ ] **Step 1: Run tests**

Run: `cd backend && uv run pytest tests/api/test_quests_api.py tests/api/test_notifications_api.py -v`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add backend/tests/api/test_quests_api.py backend/tests/api/test_notifications_api.py
git commit -m "test: add quests and notifications API tests"
```

---

### Task 15: 编写后端 Service 测试

**Files:**
- Create: `backend/tests/services/test_quest_service.py`

- [ ] **Step 1: Run tests**

Run: `cd backend && uv run pytest tests/services/test_quest_service.py -v`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add backend/tests/services/test_quest_service.py
git commit -m "test: add quest service tests"
```

---

### Task 16: 最终验证

- [ ] **Step 1: Run backend lint + typecheck + tests**

```bash
cd backend
uv run ruff check app
uv run mypy app
uv run pytest tests/api/test_quests_api.py tests/api/test_notifications_api.py tests/services/test_quest_service.py -q --tb=short
```

- [ ] **Step 2: Run frontend lint + typecheck + tests**

```bash
cd frontend
npm run lint
npm run typecheck
npm run test -- --testPathPattern="DungeonScholarQuestsPage|NotificationPopover" -q --tb=short
```

- [ ] **Step 3: Verify server starts**

Run: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
Expected: Server starts without errors

---

## 依赖关系

```
Task 1 (Migration) ──────┬──► Task 2 (Quest Model)
                         │
Task 2 ──────────────────┴──► Task 3 (Notification Model)
                                │
Task 3 ────────────────────────► Task 4 (Quest Schemas)
                                │
Task 4 ────────────────────────► Task 5 (Quest Repository)
                                │
Task 5 ────────────────────────► Task 6 (Quest Service)
                                │
Task 6 ────────────────────────► Task 7 (Notification Repo+Service)
                                │
Task 7 ────────────────────────► Task 8 (API Routes)
                                │
Task 8 ────────────────────────► Task 9 (Frontend API)
                                │
Task 9 ────────────────────────► Task 10 (Frontend Utils)
                                │
Task 10 ───────────────────────► Task 11 (i18n)
                                │
Task 11 ───────────────────────► Task 12 (QuestsPage)
                                │
Task 12 ───────────────────────► Task 13 (NotificationPopover)
                                │
Task 12, 13 ─────────────────► Task 14 (Backend API Tests)
                                │
Task 14 ───────────────────────► Task 15 (Backend Service Tests)
                                │
Task 14, 15 ─────────────────► Task 16 (Final Verification)
```

---

## 关键风险

1. **进度聚合查询性能** — 首次加载时需要聚合 runs/documents 表，建议后续加缓存
2. **连胜计算时区** — 需要统一使用 Asia/Shanghai 时区
3. **并发领取奖励** — 使用数据库唯一约束防止重复发放
4. **localStorage 迁移** — 新系统上线后需清除旧 localStorage key

---

## 复杂度评估

- **总任务数**: 16 个
- **预计实现时间**: 约 4-6 小时（按每个任务 15-20 分钟估算）
- **关键路径**: Task 1 → 8 → 12 → 16
- **可以并行**: Task 2 和 Task 3 可以并行，Task 9 和 Task 10 可以并行
