from __future__ import annotations

import json
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings, read_env_file_value
from app.db.session import get_db_session
from app.integrations.creem.client import CreemApiClient, CreemApiError, CreemApiTimeoutError
from app.schemas.payments import (
    CheckoutRequest,
    CheckoutResponse,
    RegionResponse,
    RegionUpdateRequest,
    SubscriptionResponse,
)
from app.services.payments.service import (
    CreemCheckoutError,
    PaymentConfigurationError,
    PaymentService,
)
from app.services.payments.webhook_handler import CreemWebhookHandler, WebhookSignatureError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_service(session: AsyncSession = Depends(get_db_session)) -> PaymentService:
    settings = get_settings()
    client = CreemApiClient(
        base_url=settings.creem_api_base_url,
        api_key=settings.creem_api_key or read_env_file_value("CREEM_API_KEY") or "",
    )
    return PaymentService(session=session, client=client, settings=settings)


def _subscription_product_plans() -> dict[str, str]:
    settings = get_settings()
    pairs = {
        settings.creem_product_sub_monthly or read_env_file_value("CREEM_PRODUCT_SUB_MONTHLY"): "monthly",
        settings.creem_product_sub_quarterly or read_env_file_value("CREEM_PRODUCT_SUB_QUARTERLY"): "quarterly",
        settings.creem_product_sub_yearly or read_env_file_value("CREEM_PRODUCT_SUB_YEARLY"): "yearly",
    }
    return {product_id: plan for product_id, plan in pairs.items() if product_id}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> CheckoutResponse:
    try:
        result = await service.create_checkout(user_id=user_id, product_type=payload.product_type, plan=payload.plan)
    except CreemApiTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Creem timeout") from exc
    except CreemApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Creem checkout request failed") from exc
    except PaymentConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except CreemCheckoutError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Creem checkout response is invalid") from exc
    return CheckoutResponse(**result)


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> SubscriptionResponse:
    return SubscriptionResponse(**(await service.get_subscription(user_id)))


@router.post("/subscription/cancel")
async def cancel_subscription(
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> dict[str, str]:
    return await service.cancel_subscription(user_id)


@router.get("/region", response_model=RegionResponse)
async def get_region(
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> RegionResponse:
    return RegionResponse(**(await service.get_region_pricing(user_id)))


@router.put("/region", response_model=RegionResponse)
async def update_region(
    payload: RegionUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> RegionResponse:
    return RegionResponse(**(await service.update_region(user_id, payload.region)))


@router.post("/webhook/creem")
async def creem_webhook(
    request: Request,
    creem_signature: str | None = Header(default=None),
    x_creem_signature: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    settings = get_settings()
    webhook_secret = settings.creem_webhook_secret or ""
    if not webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Creem webhook is not configured")
    handler = CreemWebhookHandler(
        session=session,
        webhook_secret=webhook_secret,
        subscription_product_plans=_subscription_product_plans(),
    )
    body = await request.body()
    try:
        handler.verify_signature(payload=body, signature=creem_signature or x_creem_signature)
    except WebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature") from exc
    try:
        event = json.loads(body.decode() or "{}")
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload")
    return await handler.handle(event)
