from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.economy import PurchaseStatus


class QuotaType(StrEnum):
    UNLIMITED = "unlimited"
    PERSONAL_CAP = "personal_cap"
    AUTO_REFILL = "auto_refill"


class ItemType(StrEnum):
    COIN_PACK = "coin_pack"
    STREAK_FREEZE = "streak_freeze"
    TIME_TREASURE = "time_treasure"
    REVIVAL = "revival"


class TierRequired(StrEnum):
    FREE = "free"
    SUPER = "super"


class ShopOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    display_name: str
    rarity: str
    price_asset_code: str
    price_amount: int
    is_active: bool
    active_from: datetime | None
    active_to: datetime | None
    purchase_limit_per_user: int | None
    # Quota / conditional access fields
    quota_type: QuotaType = QuotaType.UNLIMITED
    max_capacity: int | None = None
    refill_days: int | None = None
    tier_required: TierRequired = TierRequired.FREE
    experiment_flag: str | None = None
    item_type: ItemType = ItemType.COIN_PACK


class PurchaseRequest(BaseModel):
    offer_id: UUID
    idempotency_key: str | None = None


class PurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    offer_id: UUID | None
    item_code: str
    price_asset_code: str
    price_amount: int
    status: PurchaseStatus
    purchased_at: datetime


class BalanceResponse(BaseModel):
    asset_code: str
    balance: int


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    item_code: str
    quantity: int
    updated_at: datetime
    quota_max: int | None = None
    refill_days: int | None = None
    last_refill_at: datetime | None = None
    next_refill_at: datetime | None = None


class InventoryResponse(BaseModel):
    items: list[InventoryItemResponse]


class LeaderboardEntryResponse(BaseModel):
    user_id: UUID
    display_name: str | None
    total_xp: int
    rank: int
