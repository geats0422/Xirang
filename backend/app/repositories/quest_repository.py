from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, func, select

from app.db.models.quest import QuestAssignment, QuestStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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
        stmt = (
            select(QuestAssignment)
            .where(
                and_(
                    QuestAssignment.user_id == user_id,
                    QuestAssignment.quest_code == quest_code,
                    QuestAssignment.cycle_key == cycle_key,
                )
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quest_by_id(self, assignment_id: UUID) -> QuestAssignment | None:
        stmt = select(QuestAssignment).where(QuestAssignment.id == assignment_id).limit(1)
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

    async def count_monthly_completed(self, user_id: UUID, year_month: str) -> int:
        stmt = select(func.count(QuestAssignment.id)).where(
            and_(
                QuestAssignment.user_id == user_id,
                QuestAssignment.cycle_key.startswith(year_month),
                QuestAssignment.status.in_([QuestStatus.COMPLETED, QuestStatus.CLAIMED]),
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_monthly_completed_days(self, user_id: UUID, year_month: str) -> list[str]:
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
