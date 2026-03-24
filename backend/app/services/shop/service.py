from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol, cast

from app.db.models.economy import PurchaseStatus, QuotaType
from app.schemas.shop import (
    InventoryItemResponse,
    InventoryResponse,
    PurchaseRequest,
    PurchaseResponse,
    ShopOfferResponse,
)
from app.services.wallet.service import InsufficientBalanceError

if TYPE_CHECKING:
    from uuid import UUID


class ShopOfferProtocol(Protocol):
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
    quota_type: QuotaType
    max_capacity: int | None
    refill_days: int | None
    tier_required: str
    experiment_flag: str | None
    item_type: str


class InventoryProtocol(Protocol):
    user_id: UUID
    item_code: str
    quantity: int
    updated_at: datetime
    quota_max: int | None
    refill_days: int | None
    last_refill_at: datetime | None
    next_refill_at: datetime | None


class PurchaseRecordProtocol(Protocol):
    id: UUID
    user_id: UUID
    offer_id: UUID | None
    item_code: str
    price_asset_code: str
    price_amount: int
    status: PurchaseStatus
    purchased_at: datetime


class ShopRepositoryProtocol(Protocol):
    async def list_active_offers(self) -> list[ShopOfferProtocol]: ...
    async def get_offer(self, offer_id: UUID) -> ShopOfferProtocol | None: ...
    async def get_inventory(self, user_id: UUID) -> list[InventoryProtocol]: ...
    async def upsert_inventory(
        self,
        user_id: UUID,
        item_code: str,
        quantity: int,
        quota_max: int | None = None,
        refill_days: int | None = None,
        is_auto_refill: bool = False,
    ) -> InventoryProtocol: ...
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
    ) -> PurchaseRecordProtocol: ...
    async def get_purchase_by_idempotency_key(
        self, idempotency_key: str
    ) -> PurchaseRecordProtocol | None: ...
    async def count_purchases_by_offer(self, user_id: UUID, offer_id: UUID) -> int: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class WalletServiceProtocol(Protocol):
    async def debit(
        self,
        *,
        user_id: UUID,
        amount: int,
        asset_code: str,
        reason_code: str,
        source_type: str | None,
        source_id: UUID | None,
        idempotency_key: str | None,
    ) -> Any: ...


class ShopServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class OfferNotFoundError(ShopServiceError):
    status_code = 404


class OfferNotActiveError(ShopServiceError):
    status_code = 400


class PurchaseLimitExceededError(ShopServiceError):
    status_code = 400


class TierNotAllowedError(ShopServiceError):
    status_code = 403


class ExperimentNotActiveError(ShopServiceError):
    status_code = 422


class ShopService:
    def __init__(self, *, repository: Any, wallet_service: WalletServiceProtocol) -> None:
        self.repository: ShopRepositoryProtocol = cast("ShopRepositoryProtocol", repository)
        self.wallet_service = wallet_service

    async def list_offers(self) -> list[ShopOfferResponse]:
        offers = await self.repository.list_active_offers()
        return [ShopOfferResponse.model_validate(o) for o in offers]

    async def list_offers_for_user(
        self, user_tier: str = "free", active_experiment_flags: list[str] | None = None
    ) -> list[ShopOfferResponse]:
        offers = await self.repository.list_active_offers()
        active_flags = active_experiment_flags or []
        result: list[ShopOfferResponse] = []
        for o in offers:
            if o.tier_required == "super" and user_tier != "super":
                continue
            if o.experiment_flag is not None and o.experiment_flag not in active_flags:
                continue
            result.append(ShopOfferResponse.model_validate(o))
        return result

    async def get_inventory(self, user_id: UUID) -> InventoryResponse:
        items = await self.repository.get_inventory(user_id)
        return InventoryResponse(items=[InventoryItemResponse.model_validate(i) for i in items])

    async def purchase(self, user_id: UUID, payload: PurchaseRequest) -> PurchaseResponse:
        if payload.idempotency_key:
            existing = await self.repository.get_purchase_by_idempotency_key(
                payload.idempotency_key
            )
            if existing:
                return PurchaseResponse.model_validate(existing)

        offer = await self._get_and_validate_offer(payload.offer_id)
        await self._check_purchase_limits(user_id, offer)
        return await self._execute_purchase(user_id, offer, payload.idempotency_key)

    async def _get_and_validate_offer(self, offer_id: UUID) -> ShopOfferProtocol:
        offer = await self.repository.get_offer(offer_id)
        if offer is None:
            raise OfferNotFoundError("Offer not found")
        self._validate_offer_availability(offer)
        return offer

    def _validate_offer_availability(self, offer: ShopOfferProtocol) -> None:
        now = datetime.now(tz=UTC)
        if not offer.is_active:
            raise OfferNotActiveError("Offer is not active")
        if offer.active_from and now < offer.active_from:
            raise OfferNotActiveError("Offer is not yet active")
        if offer.active_to and now > offer.active_to:
            raise OfferNotActiveError("Offer has expired")

    async def _check_purchase_limits(self, user_id: UUID, offer: ShopOfferProtocol) -> None:
        if offer.purchase_limit_per_user is not None:
            purchase_count = await self.repository.count_purchases_by_offer(user_id, offer.id)
            if purchase_count >= offer.purchase_limit_per_user:
                raise PurchaseLimitExceededError("Purchase limit exceeded")

    async def _execute_purchase(
        self,
        user_id: UUID,
        offer: ShopOfferProtocol,
        idempotency_key: str | None,
    ) -> PurchaseResponse:
        is_auto_refill = offer.quota_type == QuotaType.AUTO_REFILL
        try:
            await self.wallet_service.debit(
                user_id=user_id,
                amount=offer.price_amount,
                asset_code=offer.price_asset_code,
                reason_code="shop_purchase",
                source_type="shop_offer",
                source_id=offer.id,
                idempotency_key=f"wallet:{idempotency_key}" if idempotency_key else None,
            )

            await self.repository.upsert_inventory(
                user_id=user_id,
                item_code=offer.item_code,
                quantity=1,
                quota_max=offer.max_capacity,
                refill_days=offer.refill_days,
                is_auto_refill=is_auto_refill,
            )

            record = await self.repository.create_purchase_record(
                user_id=user_id,
                offer_id=offer.id,
                item_code=offer.item_code,
                price_asset_code=offer.price_asset_code,
                price_amount=offer.price_amount,
                status=PurchaseStatus.COMPLETED,
                idempotency_key=idempotency_key,
            )

            await self.repository.commit()
            return PurchaseResponse.model_validate(record)

        except InsufficientBalanceError:
            await self.repository.rollback()
            raise
        except Exception:
            await self.repository.rollback()
            raise
