from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.services.notification.schemas import (
    NotificationListResponse,
    NotificationResponse,
)

if TYPE_CHECKING:
    from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self._repo = repository

    async def get_user_notifications(self, user_id: UUID) -> NotificationListResponse:
        notifications = await self._repo.get_user_notifications(user_id)
        unread_count = await self._repo.get_unread_count(user_id)

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in notifications],
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
