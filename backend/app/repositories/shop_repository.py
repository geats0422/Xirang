from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, func, or_, select

from app.db.models.economy import Inventory, PurchaseRecord, PurchaseStatus, ShopOffer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ShopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_offers(self) -> list[ShopOffer]:
        now = datetime.now(UTC)
        stmt = (
            select(ShopOffer)
            .where(
                ShopOffer.is_active.is_(True),
                or_(ShopOffer.active_from.is_(None), ShopOffer.active_from <= now),
                or_(ShopOffer.active_to.is_(None), ShopOffer.active_to >= now),
            )
            .order_by(ShopOffer.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_offer(self, offer_id: UUID) -> ShopOffer | None:
        stmt = select(ShopOffer).where(ShopOffer.id == offer_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_inventory(self, user_id: UUID) -> list[Inventory]:
        stmt = (
            select(Inventory)
            .where(Inventory.user_id == user_id)
            .order_by(Inventory.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_inventory(
        self,
        user_id: UUID,
        item_code: str,
        quantity: int,
        quota_max: int | None = None,
        refill_days: int | None = None,
        is_auto_refill: bool = False,
    ) -> Inventory:
        now = datetime.now(UTC)
        stmt = (
            select(Inventory)
            .where(and_(Inventory.user_id == user_id, Inventory.item_code == item_code))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        inventory = result.scalar_one_or_none()
        if inventory is None:
            next_refill = None
            if is_auto_refill and refill_days:
                next_refill = now + timedelta(days=refill_days)
            inventory = Inventory(
                user_id=user_id,
                item_code=item_code,
                quantity=quantity,
                quota_max=quota_max,
                refill_days=refill_days,
                last_refill_at=now,
                next_refill_at=next_refill,
            )
            self._session.add(inventory)
        else:
            if is_auto_refill:
                inventory.quantity = quota_max if quota_max else quantity
                inventory.last_refill_at = now
                if refill_days:
                    inventory.next_refill_at = now + timedelta(days=refill_days)
                if quota_max is not None:
                    inventory.quota_max = quota_max
                if refill_days is not None:
                    inventory.refill_days = refill_days
            else:
                inventory.quantity += quantity
            inventory.updated_at = now
        await self._session.flush()
        return inventory

    async def create_purchase_record(
        self,
        *,
        user_id: UUID,
        offer_id: UUID | None,
        item_code: str,
        price_asset_code: str,
        price_amount: int,
        status: PurchaseStatus,
        idempotency_key: str | None = None,
    ) -> PurchaseRecord:
        record = PurchaseRecord(
            user_id=user_id,
            offer_id=offer_id,
            item_code=item_code,
            price_asset_code=price_asset_code,
            price_amount=price_amount,
            status=status,
            idempotency_key=idempotency_key,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_purchase_by_idempotency_key(self, idempotency_key: str) -> PurchaseRecord | None:
        stmt = (
            select(PurchaseRecord).where(PurchaseRecord.idempotency_key == idempotency_key).limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_purchases_by_offer(self, user_id: UUID, offer_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(PurchaseRecord)
            .where(PurchaseRecord.user_id == user_id, PurchaseRecord.offer_id == offer_id)
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
