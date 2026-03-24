"""API routes for shop."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.shop_repository import ShopRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.shop import PurchaseRequest
from app.services.shop.service import (
    OfferNotActiveError,
    OfferNotFoundError,
    PurchaseLimitExceededError,
    ShopService,
)
from app.services.wallet.service import InsufficientBalanceError, WalletService

router = APIRouter(prefix="/shop", tags=["shop"])


async def get_shop_service(session: AsyncSession = Depends(get_db_session)) -> ShopService:
    wallet_service = WalletService(repository=WalletRepository(session))
    return ShopService(repository=ShopRepository(session), wallet_service=wallet_service)


async def get_wallet_service(session: AsyncSession = Depends(get_db_session)) -> WalletService:
    return WalletService(repository=WalletRepository(session))


async def get_wallet_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WalletRepository:
    return WalletRepository(session)


@router.get("/items")
async def list_items(
    user_tier: str | None = None,
    experiment_flags: str | None = None,
    service: ShopService = Depends(get_shop_service),
) -> list[dict[str, Any]]:
    flags = experiment_flags.split(",") if experiment_flags else []
    offers = await service.list_offers_for_user(user_tier or "free", flags)
    return [offer.model_dump(mode="json") for offer in offers]


@router.post("/purchase")
async def purchase_item(
    request: PurchaseRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: ShopService = Depends(get_shop_service),
) -> dict[str, Any]:
    try:
        result = await service.purchase(user_id, payload=request)
        return result.model_dump(mode="json")
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except OfferNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except (OfferNotActiveError, PurchaseLimitExceededError, InsufficientBalanceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/inventory")
async def get_inventory(
    user_id: UUID = Depends(get_current_user_id),
    service: ShopService = Depends(get_shop_service),
) -> dict[str, Any]:
    result = await service.get_inventory(user_id)
    return result.model_dump(mode="json")


@router.get("/balance")
async def get_balance(
    user_id: UUID = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> dict[str, Any]:
    balance = await wallet_service.get_balance(user_id, asset_code="COIN")
    return balance.model_dump(mode="json")


@router.get("/ledger")
async def get_ledger(
    user_id: UUID = Depends(get_current_user_id),
    wallet_repository: WalletRepository = Depends(get_wallet_repository),
) -> list[dict[str, Any]]:
    entries = await wallet_repository.list_ledger(user_id=user_id, asset_code="COIN")
    return [
        {
            "id": str(entry.id),
            "asset_code": entry.asset_code,
            "delta": entry.delta,
            "balance_after": entry.balance_after,
            "reason_code": entry.reason_code,
            "source_type": entry.source_type,
            "source_id": None if entry.source_id is None else str(entry.source_id),
            "created_at": entry.created_at.isoformat(),
        }
        for entry in entries
    ]


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
