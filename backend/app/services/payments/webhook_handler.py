from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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

    def verify_signature(self, *, payload: bytes, signature: str | None) -> None:
        if not signature:
            raise WebhookSignatureError("missing signature")
        expected = hmac.new(self.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise WebhookSignatureError("invalid signature")

    async def handle(self, event: dict[str, Any]) -> dict[str, bool]:
        event_id = str(event.get("id", ""))
        event_type = str(event.get("type", ""))
        data = event.get("data", {})
        user_id = data.get("user_id")
        if not event_id or not user_id:
            return {"ok": True, "ignored": True}

        existing = await self.session.execute(
            select(PaymentTransaction).where(PaymentTransaction.external_transaction_id == event_id)
        )
        if existing.scalar_one_or_none() is not None:
            return {"ok": True, "idempotent": True}

        user = await self.session.get(User, user_id)
        if user is None:
            return {"ok": True, "ignored": True}

        if event_type == "payment.succeeded":
            coins = int(data.get("coin_amount", 0))
            wallet_service = WalletService(repository=WalletRepository(self.session))
            if coins > 0:
                await wallet_service.credit(
                    user_id=user.id,
                    amount=coins,
                    reason_code="creem_payment",
                    idempotency_key=f"creem:{event_id}",
                )
            user.subscription_status = data.get("subscription_status", user.subscription_status)

        self.session.add(
            PaymentTransaction(
                user_id=user.id,
                provider_key="creem",
                external_transaction_id=event_id,
                amount=float(data.get("amount", 0)),
                currency_code=str(data.get("currency", "USD")),
                status=PaymentStatus.SUCCEEDED,
            )
        )
        await self.session.commit()
        return {"ok": True}
