from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from app.services.notification.schemas import (
    NotificationListResponse,
    NotificationResponse,
)

if TYPE_CHECKING:
    from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationMailClient(Protocol):
    async def send_notification(
        self,
        *,
        email: str,
        title: str,
        body: str | None = None,
        action_url: str | None = None,
    ) -> None: ...


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
        mail_client: NotificationMailClient | None = None,
    ) -> None:
        self._repo = repository
        self._mail_client = mail_client

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
        recipient_email: str | None = None,
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
        if self._mail_client and recipient_email:
            try:
                await self._mail_client.send_notification(
                    email=recipient_email,
                    title=title,
                    body=body,
                    action_url=action_url,
                )
            except Exception as exc:
                logger.warning(
                    "notification_email_copy_failed notification_id=%s error_type=%s",
                    notification.id,
                    exc.__class__.__name__,
                )
        return NotificationResponse.model_validate(notification)
