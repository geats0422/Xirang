from datetime import datetime

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    product_type: str
    plan: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    status: str


class RegionUpdateRequest(BaseModel):
    region: str


class RegionResponse(BaseModel):
    region: str
    prices: dict[str, float]


class SubscriptionResponse(BaseModel):
    status: str
    tier: str | None
    expires_at: datetime | None
