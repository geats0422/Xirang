from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.core.config import read_env_file_value
from app.db.models.auth import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.integrations.creem.client import CreemApiClient


PRICE_BY_REGION = {
    "premium": {"monthly": 9.6, "quarterly": 24.0, "yearly": 84.0},
    "standard": {"monthly": 8.0, "quarterly": 20.0, "yearly": 70.0},
    "developing": {"monthly": 4.0, "quarterly": 10.0, "yearly": 35.0},
}


class PaymentConfigurationError(ValueError):
    pass


class CreemCheckoutError(RuntimeError):
    pass


@dataclass
class PaymentService:
    session: AsyncSession
    client: CreemApiClient
    settings: Settings

    def resolve_region(self, country_code: str | None) -> str:
        if not country_code:
            return "standard"
        code = country_code.upper()
        if code in self.settings.premium_regions:
            return "premium"
        if code in self.settings.developing_regions:
            return "developing"
        return "standard"

    async def create_checkout(
        self,
        *,
        user_id: UUID,
        product_type: str,
        plan: str,
    ) -> dict[str, str]:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("user not found")
        product_id = self._resolve_product_id(product_type=product_type, plan=plan)
        payload = {
            "product_id": product_id,
            "success_url": self.settings.creem_checkout_success_url,
            "cancel_url": self.settings.creem_checkout_cancel_url,
            "metadata": self._build_checkout_metadata(user=user, product_type=product_type, plan=plan),
        }
        data = await self.client.create_checkout(payload)
        checkout_url = str(data.get("checkout_url") or "").strip()
        if not checkout_url:
            raise CreemCheckoutError("Creem checkout response did not include checkout_url")
        return {"checkout_url": checkout_url, "status": "created"}

    def _build_checkout_metadata(self, *, user: User, product_type: str, plan: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "user_id": str(user.id),
            "pricing_region": user.pricing_region,
            "product_type": product_type,
            "plan": plan,
        }
        if product_type == "coin":
            metadata["coin_amount"] = int(plan)
        return metadata

    def _resolve_product_id(self, *, product_type: str, plan: str) -> str:
        product_ids = {
            ("subscription", "monthly"): self.settings.creem_product_sub_monthly or read_env_file_value("CREEM_PRODUCT_SUB_MONTHLY"),
            ("subscription", "quarterly"): self.settings.creem_product_sub_quarterly or read_env_file_value("CREEM_PRODUCT_SUB_QUARTERLY"),
            ("subscription", "yearly"): self.settings.creem_product_sub_yearly or read_env_file_value("CREEM_PRODUCT_SUB_YEARLY"),
            ("coin", "60"): self.settings.creem_product_coin_60 or read_env_file_value("CREEM_PRODUCT_COIN_60"),
            ("coin", "300"): self.settings.creem_product_coin_300 or read_env_file_value("CREEM_PRODUCT_COIN_300"),
            ("coin", "680"): self.settings.creem_product_coin_680 or read_env_file_value("CREEM_PRODUCT_COIN_680"),
            ("coin", "1500"): self.settings.creem_product_coin_1500 or read_env_file_value("CREEM_PRODUCT_COIN_1500"),
            ("coin", "3500"): self.settings.creem_product_coin_3500 or read_env_file_value("CREEM_PRODUCT_COIN_3500"),
        }
        product_id = product_ids.get((product_type, plan))
        if not product_id:
            raise PaymentConfigurationError(f"Creem product is not configured: {product_type}/{plan}")
        return product_id

    async def get_region_pricing(self, user_id: UUID) -> dict[str, Any]:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("user not found")
        region = user.pricing_region or "standard"
        return {"region": region, "prices": PRICE_BY_REGION[region]}

    async def update_region(self, user_id: UUID, region: str) -> dict[str, Any]:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("user not found")
        user.pricing_region = region
        await self.session.commit()
        return await self.get_region_pricing(user_id)

    async def get_subscription(self, user_id: UUID) -> dict[str, Any]:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("user not found")
        return {
            "status": user.subscription_status,
            "tier": user.subscription_tier,
            "expires_at": user.subscription_expires_at,
        }

    async def cancel_subscription(self, user_id: UUID) -> dict[str, str]:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("user not found")
        if not user.creem_subscription_id:
            return {"status": "no_subscription"}
        await self.client.cancel_subscription(user.creem_subscription_id)
        user.subscription_status = "canceled"
        await self.session.commit()
        return {"status": "canceled"}
