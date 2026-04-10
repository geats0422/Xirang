from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

from app.schemas.quest import (
    ActionType,
    IconTone,
    MonthlyProgressResponse,
    QuestAssignmentResponse,
    QuestClaimResponse,
    QuestListResponse,
)

if TYPE_CHECKING:
    from app.db.models.quest import QuestAssignment
    from app.repositories.quest_repository import QuestRepository
    from app.repositories.shop_repository import ShopRepository
    from app.repositories.wallet_repository import WalletRepository
    from app.services.notification.schemas import NotificationResponse


class QuestDefinition:
    title_i18n_key: str
    target_metric: str
    target_value: int
    reward_type: str
    reward_item_code: str | None
    reward_i18n_key: str
    reward_icon: str
    icon: str
    icon_tone: IconTone
    action_type: ActionType
    navigate_to: str | None
    reward_asset_code: str | None
    reward_quantity: int


QUEST_DEFINITIONS: dict[str, dict[str, Any]] = {
    "quest-upload": {
        "title_i18n_key": "quests.missionUploadTitle",
        "target_metric": "document_upload",
        "target_value": 1,
        "reward_type": "item",
        "reward_item_code": "gold_chest",
        "reward_i18n_key": "quests.rewardGoldChest",
        "reward_icon": "🧰",
        "icon": "📤",
        "icon_tone": IconTone.VIOLET,
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
        "icon_tone": IconTone.AMBER,
        "action_type": ActionType.CONTINUE,
        "navigate_to": None,
    },
    "quest-abyss": {
        "title_i18n_key": "quests.missionAbyssTitle",
        "target_metric": "run_count_endless",
        "target_value": 2,
        "reward_type": "item",
        "reward_item_code": "xp_boost_2x",
        "reward_i18n_key": "quests.rewardDoubleCard",
        "reward_icon": "🎁",
        "icon": "⚔",
        "icon_tone": IconTone.VIOLET,
        "action_type": ActionType.CONTINUE,
        "navigate_to": None,
    },
    "quest-accuracy": {
        "title_i18n_key": "quests.missionAccuracyTitle",
        "target_metric": "accuracy_gte_80",
        "target_value": 1,
        "reward_type": "asset",
        "reward_asset_code": "COIN",
        "reward_quantity": 30,
        "reward_i18n_key": "quests.rewardCoins30",
        "reward_icon": "🪙",
        "icon": "✪",
        "icon_tone": IconTone.GREEN,
        "action_type": ActionType.CONTINUE,
        "navigate_to": None,
    },
    "quest-time": {
        "title_i18n_key": "quests.missionTimeTitle",
        "target_metric": "study_minutes",
        "target_value": 10,
        "reward_type": "asset",
        "reward_asset_code": "COIN",
        "reward_quantity": 20,
        "reward_i18n_key": "quests.rewardCoins20",
        "reward_icon": "🪙",
        "icon": "⏱",
        "icon_tone": IconTone.BLUE,
        "action_type": ActionType.CONTINUE,
        "navigate_to": None,
    },
    "quest-floors": {
        "title_i18n_key": "quests.missionFloorsTitle",
        "target_metric": "endless_floors",
        "target_value": 5,
        "reward_type": "asset",
        "reward_asset_code": "COIN",
        "reward_quantity": 25,
        "reward_i18n_key": "quests.rewardCoins25",
        "reward_icon": "🪙",
        "icon": "🗼",
        "icon_tone": IconTone.AMBER,
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


class NotificationServiceProtocol(Protocol):
    async def create_notification(
        self,
        *,
        user_id: UUID,
        type: str,
        title: str,
        body: str | None = None,
        related_quest_id: UUID | None = None,
        action_url: str | None = None,
    ) -> NotificationResponse: ...


class QuestService:
    def __init__(
        self,
        quest_repository: QuestRepository,
        wallet_repository: WalletRepository,
        shop_repository: ShopRepository,
        notification_service: NotificationServiceProtocol,
    ) -> None:
        self._quest_repo = quest_repository
        self._wallet_repo = wallet_repository
        self._shop_repo = shop_repository
        self._notification_service = notification_service

    def _get_today_cycle_key(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _get_month_cycle_key(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m")

    def _get_month_days_remaining(self) -> int:
        now = datetime.now(UTC)
        total_days = (
            (datetime(now.year, now.month + 1, 1) - datetime(now.year, now.month, 1)).days
            if now.month < 12
            else 31
        )
        return total_days - now.day

    async def _get_monthly_progress(self, user_id: UUID) -> MonthlyProgressResponse:
        year_month = self._get_month_cycle_key()
        completed_days = await self._quest_repo.get_monthly_completed_days(user_id, year_month)
        return MonthlyProgressResponse(
            current=len(completed_days),
            target=30,
            year_month=year_month,
            days_remaining=self._get_month_days_remaining(),
            completed_day_keys=completed_days,
        )

    def _build_quest_response(self, quest: QuestAssignment) -> QuestAssignmentResponse:
        definition = QUEST_DEFINITIONS.get(
            quest.quest_code,
            {
                "title_i18n_key": f"quests.{quest.quest_code}Title",
                "icon": "✦",
                "icon_tone": IconTone.BLUE,
            },
        )
        action_i18n = (
            "quests.claimReward"
            if quest.status == "completed"
            else (
                "quests.upload"
                if definition.get("action_type") == ActionType.NAVIGATE
                else "quests.continue"
            )
        )
        return QuestAssignmentResponse(
            id=quest.id,
            quest_code=quest.quest_code,
            quest_type=quest.quest_type,
            title_i18n_key=definition.get("title_i18n_key", f"quests.{quest.quest_code}Title"),
            description_i18n_key="",
            target_metric=quest.target_metric,
            target_value=quest.target_value,
            progress_value=quest.progress_value,
            status=quest.status,
            reward_type=quest.reward_type,
            reward_asset_code=quest.reward_asset_code,
            reward_quantity=quest.reward_quantity,
            reward_item_code=quest.reward_item_code,
            reward_i18n_key=definition.get("reward_i18n_key", ""),
            reward_icon=definition.get("reward_icon", "🎁"),
            action_i18n_key=action_i18n,
            action_type=definition.get("action_type", ActionType.CONTINUE),
            navigate_to=definition.get("navigate_to"),
            icon=definition.get("icon", "✦"),
            icon_tone=definition.get("icon_tone", IconTone.BLUE),
            expires_at=quest.expires_at,
            locked=False,
        )

    async def get_user_quests(self, user_id: UUID) -> QuestListResponse:
        today_key = self._get_today_cycle_key()
        await self._ensure_daily_quests(user_id, today_key)
        quests = await self._quest_repo.get_user_quests_by_cycle(user_id, today_key)

        quest_order = {code: index for index, code in enumerate(QUEST_DEFINITIONS.keys())}
        quests.sort(key=lambda q: quest_order.get(q.quest_code, 999))

        quest_responses = [self._build_quest_response(q) for q in quests]
        monthly_progress = await self._get_monthly_progress(user_id)

        now = datetime.now(UTC)
        refresh_at = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=UTC)

        return QuestListResponse(
            daily_quests=quest_responses,
            daily_refresh_at=refresh_at,
            monthly_progress=monthly_progress,
            streak_days=0,
            streak_milestone=None,
        )

    async def _ensure_daily_quests(self, user_id: UUID, cycle_key: str) -> list[QuestAssignment]:
        quests = []
        for quest_code, definition in QUEST_DEFINITIONS.items():
            existing = await self._quest_repo.get_user_quest(user_id, quest_code, cycle_key)
            if not existing:
                expires_at = datetime.strptime(
                    cycle_key + " 23:59:59", "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=UTC)
                quest = await self._quest_repo.create_quest(
                    user_id=user_id,
                    quest_code=quest_code,
                    quest_type="daily",
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

    async def claim_reward(self, user_id: UUID, assignment_id: UUID) -> QuestClaimResponse:
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

        coin_balance: int | None = None
        item_quantity: int | None = None

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
            inventory = await self._shop_repo.upsert_inventory(
                user_id=user_id,
                item_code=quest.reward_item_code,
                quantity=1,
            )
            item_quantity = inventory.quantity

        await self._notification_service.create_notification(
            user_id=user_id,
            type="quest_claimed",
            title="Reward claimed",
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
