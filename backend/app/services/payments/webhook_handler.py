from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select

from app.db.models.auth import User
from app.db.models.economy import PaymentStatus, PaymentTransaction
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet.service import WalletService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class WebhookSignatureError(Exception):
    pass


@dataclass
class CreemWebhookHandler:
    session: AsyncSession
    webhook_secret: str
    subscription_product_plans: dict[str, str] | None = None

    def verify_signature(self, *, payload: bytes, signature: str | None) -> None:
        if not self.webhook_secret or not signature:
            raise WebhookSignatureError("missing signature")
        expected = hmac.new(self.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise WebhookSignatureError("invalid signature")

    async def handle(self, event: dict[str, Any]) -> dict[str, bool]:
        event_id = str(event.get("id", ""))
        event_type = str(event.get("eventType") or event.get("type") or "")
        event_object_raw = event.get("object")
        legacy_data_raw = event.get("data")
        event_object: dict[str, Any] = event_object_raw if isinstance(event_object_raw, dict) else {}
        legacy_data: dict[str, Any] = legacy_data_raw if isinstance(legacy_data_raw, dict) else {}
        data: dict[str, Any] = event_object or legacy_data
        metadata = self._extract_metadata(data)
        user_id = metadata.get("user_id") or metadata.get("referenceId") or legacy_data.get("user_id")
        if not event_id or not user_id:
            return {"ok": True, "ignored": True}

        existing = await self.session.execute(
            select(PaymentTransaction).where(PaymentTransaction.external_transaction_id == event_id)
        )
        if existing.scalar_one_or_none() is not None:
            return {"ok": True, "idempotent": True}

        try:
            parsed_user_id = UUID(str(user_id))
        except ValueError:
            return {"ok": True, "ignored": True}

        user = await self.session.get(User, parsed_user_id)
        if user is None:
            return {"ok": True, "ignored": True}

        if event_type in {"payment.succeeded", "checkout.completed"}:
            coins = self._safe_int(metadata.get("coin_amount") or legacy_data.get("coin_amount") or 0)
            wallet_service = WalletService(repository=WalletRepository(self.session))
            if coins > 0:
                await wallet_service.credit(
                    user_id=user.id,
                    amount=coins,
                    reason_code="creem_payment",
                    idempotency_key=f"creem:{event_id}",
                )
            if (metadata.get("product_type") == "subscription" or data.get("subscription")) and self._is_configured_subscription(data):
                self._activate_subscription(user=user, data=data, metadata=metadata)

        if event_type in {"subscription.paid", "subscription.active", "subscription.trialing"} and self._is_configured_subscription(data):
            self._activate_subscription(user=user, data=data, metadata=metadata)

        if event_type in {"subscription.canceled", "subscription.expired"}:
            user.subscription_status = "canceled"

        if event_type == "subscription.past_due":
            user.subscription_status = "past_due"

        if event_type == "subscription.paused":
            user.subscription_status = "paused"

        self.session.add(
            PaymentTransaction(
                user_id=user.id,
                provider_key="creem",
                external_transaction_id=event_id,
                amount=self._extract_amount(data),
                currency_code=self._extract_currency(data),
                status=PaymentStatus.SUCCEEDED,
            )
        )
        await self.session.commit()
        return {"ok": True}

    def _extract_metadata(self, data: dict[str, Any]) -> dict[str, Any]:
        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            return dict(metadata)
        subscription = data.get("subscription")
        if isinstance(subscription, dict) and isinstance(subscription.get("metadata"), dict):
            return dict(subscription["metadata"])
        return {}

    def _activate_subscription(self, *, user: User, data: dict[str, Any], metadata: dict[str, Any]) -> None:
        subscription_raw = data.get("subscription")
        subscription: dict[str, Any] = subscription_raw if isinstance(subscription_raw, dict) else data
        customer_raw = data.get("customer") or subscription.get("customer")
        customer: dict[str, Any] | None = customer_raw if isinstance(customer_raw, dict) else None
        user.subscription_status = "active"
        product_id = self._extract_product_id(data)
        product_plan = (self.subscription_product_plans or {}).get(product_id or "")
        user.subscription_tier = str(metadata.get("plan") or product_plan or user.subscription_tier or "monthly")
        user.creem_subscription_id = str(subscription.get("id") or user.creem_subscription_id or "") or None
        if customer is not None:
            user.creem_customer_id = str(customer.get("id") or user.creem_customer_id or "") or None
        period_end = subscription.get("current_period_end_date")
        if isinstance(period_end, str):
            user.subscription_expires_at = self._parse_creem_datetime(period_end)

    def _parse_creem_datetime(self, value: str) -> datetime | None:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _extract_amount(self, data: dict[str, Any]) -> float:
        order_raw = data.get("order")
        product_raw = data.get("product")
        order: dict[str, Any] = order_raw if isinstance(order_raw, dict) else {}
        product: dict[str, Any] = product_raw if isinstance(product_raw, dict) else {}
        amount = data.get("amount") or order.get("amount_paid") or order.get("amount") or product.get("price") or 0
        return self._safe_float(amount)

    def _extract_currency(self, data: dict[str, Any]) -> str:
        order_raw = data.get("order")
        product_raw = data.get("product")
        order: dict[str, Any] = order_raw if isinstance(order_raw, dict) else {}
        product: dict[str, Any] = product_raw if isinstance(product_raw, dict) else {}
        return str(data.get("currency") or order.get("currency") or product.get("currency") or "USD")

    def _extract_product_id(self, data: dict[str, Any]) -> str | None:
        product = data.get("product")
        if isinstance(product, dict):
            product_id = product.get("id")
            return str(product_id) if product_id else None
        if isinstance(product, str):
            return product
        subscription = data.get("subscription")
        if isinstance(subscription, dict):
            subscription_product = subscription.get("product")
            if isinstance(subscription_product, dict):
                product_id = subscription_product.get("id")
                return str(product_id) if product_id else None
            if isinstance(subscription_product, str):
                return subscription_product
        return None

    def _is_configured_subscription(self, data: dict[str, Any]) -> bool:
        allowed_products = self.subscription_product_plans or {}
        product_id = self._extract_product_id(data)
        return bool(product_id and product_id in allowed_products)

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
