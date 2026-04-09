from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, select, update

from app.db.models.notification import Notification

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_notifications(self, user_id: UUID, limit: int = 50) -> list[Notification]:
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
            and_(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
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
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))  # noqa: E712
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[no-any-return,attr-defined]

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
