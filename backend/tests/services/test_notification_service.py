from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.services.notification.schemas import NotificationListResponse
from app.services.notification.service import NotificationService

pytestmark = pytest.mark.asyncio(loop_scope="module")


class FakeNotification:
    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        type: str,
        title: str,
        body: str | None = None,
        is_read: bool = False,
        related_quest_id: UUID | None = None,
        action_url: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.type = type
        self.title = title
        self.body = body
        self.is_read = is_read
        self.related_quest_id = related_quest_id
        self.action_url = action_url
        self.created_at = created_at or datetime.now(UTC)


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.notifications: dict[UUID, FakeNotification] = {}
        self.committed = False

    async def get_user_notifications(self, user_id: UUID) -> list[FakeNotification]:
        return [n for n in self.notifications.values() if n.user_id == user_id]

    async def get_unread_count(self, user_id: UUID) -> int:
        return sum(1 for n in self.notifications.values() if n.user_id == user_id and not n.is_read)

    async def mark_read(self, notification_id: UUID) -> FakeNotification | None:
        notification = self.notifications.get(notification_id)
        if notification:
            notification.is_read = True
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        count = 0
        for n in self.notifications.values():
            if n.user_id == user_id and not n.is_read:
                n.is_read = True
                count += 1
        return count

    async def create_notification(
        self,
        *,
        user_id: UUID,
        type: str,
        title: str,
        body: str | None = None,
        related_quest_id: UUID | None = None,
        action_url: str | None = None,
    ) -> FakeNotification:
        notification = FakeNotification(
            id=uuid4(),
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            is_read=False,
            related_quest_id=related_quest_id,
            action_url=action_url,
            created_at=datetime.now(UTC),
        )
        self.notifications[notification.id] = notification
        return notification

    async def commit(self) -> None:
        self.committed = True


class TestNotificationService:
    async def test_get_user_notifications_empty(self) -> None:
        repo = FakeNotificationRepository()
        service = NotificationService(repo)
        user_id = uuid4()

        result = await service.get_user_notifications(user_id)

        assert isinstance(result, NotificationListResponse)
        assert len(result.items) == 0
        assert result.unread_count == 0

    async def test_get_user_notifications_with_data(self) -> None:
        repo = FakeNotificationRepository()
        service = NotificationService(repo)
        user_id = uuid4()

        await repo.create_notification(
            user_id=user_id,
            type="quest_claimed",
            title="Reward claimed!",
            body="You claimed your reward.",
        )
        await repo.create_notification(
            user_id=user_id,
            type="quest_reward",
            title="Quest available!",
            body=None,
        )
        await repo.create_notification(
            user_id=uuid4(),
            type="system",
            title="Other user notification",
        )

        result = await service.get_user_notifications(user_id)

        assert isinstance(result, NotificationListResponse)
        assert len(result.items) == 2
        assert result.unread_count == 2

    async def test_mark_read(self) -> None:
        repo = FakeNotificationRepository()
        service = NotificationService(repo)
        user_id = uuid4()

        notification = await repo.create_notification(
            user_id=user_id,
            type="quest_claimed",
            title="Reward claimed!",
        )

        result = await service.mark_read(notification.id)

        assert result is not None
        assert result.is_read is True
        assert await repo.get_unread_count(user_id) == 0

    async def test_mark_read_not_found(self) -> None:
        repo = FakeNotificationRepository()
        service = NotificationService(repo)

        result = await service.mark_read(uuid4())

        assert result is None

    async def test_mark_all_read(self) -> None:
        repo = FakeNotificationRepository()
        service = NotificationService(repo)
        user_id = uuid4()

        await repo.create_notification(
            user_id=user_id, type="quest_claimed", title="Notification 1"
        )
        await repo.create_notification(user_id=user_id, type="quest_reward", title="Notification 2")
        await repo.create_notification(
            user_id=user_id, type="streak_warning", title="Notification 3"
        )

        count = await service.mark_all_read(user_id)

        assert count == 3
        assert await repo.get_unread_count(user_id) == 0

    async def test_create_notification(self) -> None:
        repo = FakeNotificationRepository()
        service = NotificationService(repo)
        user_id = uuid4()
        quest_id = uuid4()

        result = await service.create_notification(
            user_id=user_id,
            type="quest_reward",
            title="New quest available",
            body="Check out your new daily quests!",
            related_quest_id=quest_id,
            action_url="/quests",
        )

        assert result.type == "quest_reward"
        assert result.title == "New quest available"
        assert result.body == "Check out your new daily quests!"
        assert result.related_quest_id == quest_id
        assert result.action_url == "/quests"
        assert result.is_read is False
