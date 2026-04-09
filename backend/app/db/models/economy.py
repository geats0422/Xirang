from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class PurchaseStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class LeaderboardScope(StrEnum):
    GLOBAL = "global"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class QuotaType(StrEnum):
    UNLIMITED = "unlimited"
    PERSONAL_CAP = "personal_cap"
    AUTO_REFILL = "auto_refill"


class ItemType(StrEnum):
    COIN_PACK = "coin_pack"
    STREAK_FREEZE = "streak_freeze"
    XP_BOOST = "xp_boost"
    TIME_TREASURE = "time_treasure"
    REVIVAL = "revival"


class TierRequired(StrEnum):
    FREE = "free"
    SUPER = "super"


class Wallet(Base):
    __tablename__ = "wallets"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class WalletLedger(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "wallet_ledger"
    __table_args__ = (
        Index("ux_wallet_ledger_idempotency_key", "idempotency_key", unique=True),
        Index("ix_wallet_ledger_user_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    asset_code: Mapped[str] = mapped_column(String(40), nullable=False)
    delta: Mapped[int] = mapped_column(nullable=False)
    balance_after: Mapped[int] = mapped_column(nullable=False)
    reason_code: Mapped[str] = mapped_column(String(60), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(60))
    source_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Inventory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inventories"
    __table_args__ = (UniqueConstraint("user_id", "item_code"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_code: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
    quota_max: Mapped[int | None] = mapped_column(nullable=True)
    refill_days: Mapped[int | None] = mapped_column(nullable=True)
    last_refill_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_refill_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ShopOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shop_offers"

    item_code: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False)
    price_asset_code: Mapped[str] = mapped_column(String(40), nullable=False)
    price_amount: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    active_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purchase_limit_per_user: Mapped[int | None] = mapped_column()
    quota_type: Mapped[QuotaType] = mapped_column(
        Enum(QuotaType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=QuotaType.UNLIMITED,
        server_default=QuotaType.UNLIMITED.value,
    )
    max_capacity: Mapped[int | None] = mapped_column(nullable=True)
    refill_days: Mapped[int | None] = mapped_column(nullable=True)
    tier_required: Mapped[TierRequired] = mapped_column(
        Enum(TierRequired, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=TierRequired.FREE,
        server_default=TierRequired.FREE.value,
    )
    experiment_flag: Mapped[str | None] = mapped_column(String(80), nullable=True)
    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=ItemType.COIN_PACK,
        server_default=ItemType.COIN_PACK.value,
    )


class PaymentTransaction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "payment_transactions"

    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    provider_key: Mapped[str] = mapped_column(String(40), nullable=False)
    external_transaction_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class PurchaseRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "purchase_records"
    __table_args__ = (Index("ux_purchase_records_idempotency_key", "idempotency_key", unique=True),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    offer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shop_offers.id", ondelete="SET NULL")
    )
    payment_transaction_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payment_transactions.id", ondelete="SET NULL"),
    )
    item_code: Mapped[str] = mapped_column(String(80), nullable=False)
    price_asset_code: Mapped[str] = mapped_column(String(40), nullable=False)
    price_amount: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(
            PurchaseStatus, native_enum=False, create_constraint=True, values_callable=enum_values
        ),
        nullable=False,
        default=PurchaseStatus.COMPLETED,
        server_default=PurchaseStatus.COMPLETED.value,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class LeaderboardSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "leaderboard_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "leaderboard_scope", "snapshot_date"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    season_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("seasons.id", ondelete="SET NULL")
    )
    leaderboard_scope: Mapped[LeaderboardScope] = mapped_column(
        Enum(
            LeaderboardScope, native_enum=False, create_constraint=True, values_callable=enum_values
        ),
        nullable=False,
        default=LeaderboardScope.GLOBAL,
        server_default=LeaderboardScope.GLOBAL.value,
    )
    xp_total: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    rank_position: Mapped[int | None] = mapped_column()
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)


class ActiveEffect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "active_effects"
    __table_args__ = (
        UniqueConstraint("user_id", "effect_type", name="uq_active_effects_user_type"),
        Index("ix_active_effects_user_expires", "user_id", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    effect_type: Mapped[str] = mapped_column(String(40), nullable=False)
    multiplier: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_item_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_use_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class UseRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "use_records"
    __table_args__ = (Index("ix_use_records_user_used_at", "user_id", "used_at"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_code: Mapped[str] = mapped_column(String(80), nullable=False)
    inventory_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("inventories.id", ondelete="SET NULL"), nullable=True
    )
    effect_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
