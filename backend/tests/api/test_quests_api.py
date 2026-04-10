from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.db.models.quest import QuestStatus
from app.schemas.quest import (
    MonthlyProgressResponse,
    QuestListResponse,
)
from app.services.notification.schemas import NotificationResponse

pytestmark = pytest.mark.asyncio(loop_scope="module")


@dataclass
class FakeQuestAssignment:
    id: UUID
    user_id: UUID
    quest_code: str
    quest_type: str
    target_metric: str
    target_value: int
    progress_value: int
    cycle_key: str
    status: QuestStatus
    reward_type: str
    reward_asset_code: str | None
    reward_quantity: int
    reward_item_code: str | None
    assigned_at: datetime
    expires_at: datetime | None
    completed_at: datetime | None
    claimed_at: datetime | None


class FakeQuestRepository:
    def __init__(self) -> None:
        self.quests: dict[UUID, FakeQuestAssignment] = {}
        self.committed = False

    async def get_user_quests_by_cycle(
        self, user_id: UUID, cycle_key: str
    ) -> list[FakeQuestAssignment]:
        return [
            q for q in self.quests.values() if q.user_id == user_id and q.cycle_key == cycle_key
        ]

    async def get_user_quest(
        self, user_id: UUID, quest_code: str, cycle_key: str
    ) -> FakeQuestAssignment | None:
        for q in self.quests.values():
            if q.user_id == user_id and q.quest_code == quest_code and q.cycle_key == cycle_key:
                return q
        return None

    async def get_quest_by_id(self, assignment_id: UUID) -> FakeQuestAssignment | None:
        return self.quests.get(assignment_id)

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
    ) -> FakeQuestAssignment:
        quest = FakeQuestAssignment(
            id=uuid4(),
            user_id=user_id,
            quest_code=quest_code,
            quest_type=quest_type,
            target_metric=target_metric,
            target_value=target_value,
            progress_value=0,
            cycle_key=cycle_key,
            status=QuestStatus.IN_PROGRESS,
            reward_type=reward_type,
            reward_asset_code=reward_asset_code,
            reward_quantity=reward_quantity,
            reward_item_code=reward_item_code,
            assigned_at=datetime.now(UTC),
            expires_at=expires_at,
            completed_at=None,
            claimed_at=None,
        )
        self.quests[quest.id] = quest
        return quest

    async def update_progress(
        self,
        assignment_id: UUID,
        progress_value: int,
        status: QuestStatus | None = None,
    ) -> FakeQuestAssignment | None:
        quest = self.quests.get(assignment_id)
        if quest is None:
            return None
        quest.progress_value = progress_value
        if status:
            quest.status = status
            if status == QuestStatus.COMPLETED:
                quest.completed_at = datetime.now(UTC)
        return quest

    async def mark_claimed(self, assignment_id: UUID) -> FakeQuestAssignment | None:
        quest = self.quests.get(assignment_id)
        if quest is None:
            return None
        quest.status = QuestStatus.CLAIMED
        quest.claimed_at = datetime.now(UTC)
        return quest

    async def mark_expired(self, assignment_id: UUID) -> FakeQuestAssignment | None:
        quest = self.quests.get(assignment_id)
        if quest is None:
            return None
        quest.status = QuestStatus.EXPIRED
        return quest

    async def count_monthly_completed(self, user_id: UUID, year_month: str) -> int:
        return sum(
            1
            for q in self.quests.values()
            if q.user_id == user_id
            and q.cycle_key.startswith(year_month)
            and q.status in (QuestStatus.COMPLETED, QuestStatus.CLAIMED)
        )

    async def get_monthly_completed_days(self, user_id: UUID, year_month: str) -> list[str]:
        days: set[str] = set()
        for q in self.quests.values():
            if (
                q.user_id == user_id
                and q.cycle_key.startswith(year_month)
                and q.status in (QuestStatus.COMPLETED, QuestStatus.CLAIMED)
                and q.quest_type == "daily"
            ):
                days.add(q.cycle_key)
        return sorted(days)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


class FakeWalletRepository:
    def __init__(self) -> None:
        self.ledger: dict[str, list] = {}

    async def create_ledger_entry(
        self,
        *,
        user_id: UUID,
        asset_code: str,
        delta: int,
        reason_code: str,
        source_type: str | None = None,
        source_id: UUID | None = None,
    ) -> None:
        key = f"{user_id}:{asset_code}"
        if key not in self.ledger:
            self.ledger[key] = []
        self.ledger[key].append({"delta": delta, "reason_code": reason_code})

    async def get_balance(self, user_id: UUID, asset_code: str) -> int:
        key = f"{user_id}:{asset_code}"
        entries = self.ledger.get(key, [])
        return sum(e["delta"] for e in entries)


class FakeNotificationRepo:
    def __init__(self) -> None:
        self.notifications: list[FakeQuestAssignment] = []
        self.created: list = []

    async def get_user_notifications(self, user_id: UUID) -> list:
        return [n for n in self.notifications if n.user_id == user_id]

    async def get_unread_count(self, user_id: UUID) -> int:
        return sum(
            1
            for n in self.notifications
            if n.user_id == user_id and not getattr(n, "is_read", True)
        )

    async def mark_read(self, notification_id: UUID):
        pass

    async def mark_all_read(self, user_id: UUID) -> int:
        count = 0
        for n in self.notifications:
            if n.user_id == user_id and not getattr(n, "is_read", True):
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
    ) -> NotificationResponse:
        self.created.append(
            {
                "user_id": user_id,
                "type": type,
                "title": title,
                "body": body,
                "related_quest_id": related_quest_id,
                "action_url": action_url,
            }
        )
        return NotificationResponse(
            id=uuid4(),
            type=type,
            title=title,
            body=body,
            is_read=False,
            related_quest_id=related_quest_id,
            action_url=action_url,
            created_at=datetime.now(UTC),
        )

    async def commit(self) -> None:
        pass


class FakeShopRepository:
    def __init__(self) -> None:
        self.inventory: dict[tuple[UUID, str], int] = {}

    async def upsert_inventory(
        self,
        user_id: UUID,
        item_code: str,
        quantity: int,
        quota_max: int | None = None,
        refill_days: int | None = None,
        is_auto_refill: bool = False,
    ):
        current = self.inventory.get((user_id, item_code), 0)
        updated = current + quantity
        self.inventory[(user_id, item_code)] = updated

        class InventoryResult:
            def __init__(self, qty: int) -> None:
                self.quantity = qty

        return InventoryResult(updated)


class TestQuestService:
    async def test_get_user_quests_creates_daily_quests(self) -> None:
        from app.services.quest.service import QuestService

        user_id = uuid4()
        repo = FakeQuestRepository()
        wallet_repo = FakeWalletRepository()
        notification_repo = FakeNotificationRepo()
        shop_repo = FakeShopRepository()

        service = QuestService(
            quest_repository=repo,
            wallet_repository=wallet_repo,
            shop_repository=shop_repo,
            notification_service=notification_repo,
        )

        result = await service.get_user_quests(user_id)

        assert isinstance(result, QuestListResponse)
        assert len(result.daily_quests) >= 0
        assert result.monthly_progress is not None
        assert isinstance(result.monthly_progress, MonthlyProgressResponse)

    async def test_claim_reward_success(self) -> None:
        from app.services.quest.service import QuestService

        user_id = uuid4()
        repo = FakeQuestRepository()
        wallet_repo = FakeWalletRepository()
        notification_repo = FakeNotificationRepo()
        shop_repo = FakeShopRepository()

        service = QuestService(
            quest_repository=repo,
            wallet_repository=wallet_repo,
            shop_repository=shop_repo,
            notification_service=notification_repo,
        )

        now = datetime.now(UTC)
        cycle_key = now.strftime("%Y-%m-%d")

        quest = await repo.create_quest(
            user_id=user_id,
            quest_code="quest-streak",
            quest_type="daily",
            target_metric="streak",
            target_value=1,
            cycle_key=cycle_key,
            reward_type="asset",
            reward_asset_code="COIN",
            reward_quantity=50,
        )
        await repo.update_progress(quest.id, 1, QuestStatus.COMPLETED)

        result = await service.claim_reward(user_id, quest.id)

        assert result.status == "claimed"
        assert result.reward_asset_code == "COIN"
        assert result.reward_quantity == 50
        assert len(notification_repo.created) == 1

    async def test_claim_reward_quest_not_found(self) -> None:
        from app.services.quest.service import QuestNotFoundError, QuestService

        user_id = uuid4()
        repo = FakeQuestRepository()
        wallet_repo = FakeWalletRepository()
        notification_repo = FakeNotificationRepo()
        shop_repo = FakeShopRepository()

        service = QuestService(
            quest_repository=repo,
            wallet_repository=wallet_repo,
            shop_repository=shop_repo,
            notification_service=notification_repo,
        )

        with pytest.raises(QuestNotFoundError):
            await service.claim_reward(user_id, uuid4())

    async def test_claim_reward_not_completed(self) -> None:
        from app.services.quest.service import QuestNotCompletedError, QuestService

        user_id = uuid4()
        repo = FakeQuestRepository()
        wallet_repo = FakeWalletRepository()
        notification_repo = FakeNotificationRepo()
        shop_repo = FakeShopRepository()

        service = QuestService(
            quest_repository=repo,
            wallet_repository=wallet_repo,
            shop_repository=shop_repo,
            notification_service=notification_repo,
        )

        now = datetime.now(UTC)
        cycle_key = now.strftime("%Y-%m-%d")

        quest = await repo.create_quest(
            user_id=user_id,
            quest_code="quest-streak",
            quest_type="daily",
            target_metric="streak",
            target_value=1,
            cycle_key=cycle_key,
            reward_type="asset",
            reward_asset_code="COIN",
            reward_quantity=50,
        )

        with pytest.raises(QuestNotCompletedError):
            await service.claim_reward(user_id, quest.id)

    async def test_claim_reward_already_claimed(self) -> None:
        from app.services.quest.service import QuestAlreadyClaimedError, QuestService

        user_id = uuid4()
        repo = FakeQuestRepository()
        wallet_repo = FakeWalletRepository()
        notification_repo = FakeNotificationRepo()
        shop_repo = FakeShopRepository()

        service = QuestService(
            quest_repository=repo,
            wallet_repository=wallet_repo,
            shop_repository=shop_repo,
            notification_service=notification_repo,
        )

        now = datetime.now(UTC)
        cycle_key = now.strftime("%Y-%m-%d")

        quest = await repo.create_quest(
            user_id=user_id,
            quest_code="quest-streak",
            quest_type="daily",
            target_metric="streak",
            target_value=1,
            cycle_key=cycle_key,
            reward_type="asset",
            reward_asset_code="COIN",
            reward_quantity=50,
        )
        await repo.update_progress(quest.id, 1, QuestStatus.COMPLETED)
        await repo.mark_claimed(quest.id)

        with pytest.raises(QuestAlreadyClaimedError):
            await service.claim_reward(user_id, quest.id)
