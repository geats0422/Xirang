from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.payments.service import CreemCheckoutError, PaymentService


class FakeClient:
    def __init__(self, checkout_url: str = "https://checkout.local") -> None:
        self.payload = None
        self.checkout_url = checkout_url

    async def create_checkout(self, payload):  # type: ignore[no-untyped-def]
        self.payload = payload
        return {"checkout_url": self.checkout_url}

    async def cancel_subscription(self, subscription_id: str):  # type: ignore[no-untyped-def]
        return {"ok": True}


class FakeUser:
    def __init__(self) -> None:
        self.id = uuid4()
        self.pricing_region = "standard"
        self.subscription_status = "free"
        self.subscription_tier = None
        self.subscription_expires_at = None
        self.creem_subscription_id = "sub_1"


class FakeSession:
    def __init__(self) -> None:
        self.user = FakeUser()

    async def get(self, model, user_id):  # type: ignore[no-untyped-def]
        return self.user if user_id == self.user.id else None

    async def commit(self) -> None:
        return None


@pytest.mark.asyncio(loop_scope="module")
async def test_region_fallback_standard() -> None:
    service = PaymentService(
        session=FakeSession(),  # type: ignore[arg-type]
        client=FakeClient(),  # type: ignore[arg-type]
        settings=Settings(),
    )
    assert service.resolve_region("ZZ") == "standard"


@pytest.mark.asyncio(loop_scope="module")
async def test_create_checkout_returns_url() -> None:
    session = FakeSession()
    client = FakeClient()
    service = PaymentService(
        session=session,
        client=client,
        settings=Settings(creem_product_sub_monthly="prod_monthly"),
    )  # type: ignore[arg-type]
    result = await service.create_checkout(user_id=session.user.id, product_type="subscription", plan="monthly")
    assert result["checkout_url"] == "https://checkout.local"
    assert client.payload["product_id"] == "prod_monthly"
    assert "cancel_url" not in client.payload


@pytest.mark.asyncio(loop_scope="module")
async def test_create_coin_checkout_uses_coin_product_id() -> None:
    session = FakeSession()
    client = FakeClient()
    service = PaymentService(
        session=session,
        client=client,
        settings=Settings(creem_product_coin_1500="prod_coin_1500"),
    )  # type: ignore[arg-type]
    result = await service.create_checkout(user_id=session.user.id, product_type="coin", plan="1500")
    assert result["checkout_url"] == "https://checkout.local"
    assert client.payload["product_id"] == "prod_coin_1500"
    assert client.payload["metadata"]["coin_amount"] == 1500


@pytest.mark.asyncio(loop_scope="module")
async def test_create_checkout_rejects_empty_checkout_url() -> None:
    session = FakeSession()
    service = PaymentService(
        session=session,
        client=FakeClient(checkout_url=""),
        settings=Settings(creem_product_sub_monthly="prod_monthly"),
    )  # type: ignore[arg-type]

    with pytest.raises(CreemCheckoutError):
        await service.create_checkout(user_id=session.user.id, product_type="subscription", plan="monthly")


@pytest.mark.asyncio(loop_scope="module")
async def test_cancel_subscription_success() -> None:
    session = FakeSession()
    service = PaymentService(session=session, client=FakeClient(), settings=Settings())  # type: ignore[arg-type]
    result = await service.cancel_subscription(session.user.id)
    assert result["status"] == "canceled"
