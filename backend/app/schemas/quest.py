from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)

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
    streak_milestone: dict[str, str] | None


class QuestClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: UUID
    status: Literal["claimed"]
    reward_type: str
    reward_asset_code: str | None
    reward_quantity: int
    reward_item_code: str | None
    coin_balance_after: int | None
    item_quantity_after: int | None
