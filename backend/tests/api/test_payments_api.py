import hashlib
import hmac
import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user_id
from app.api.v1.payments import get_payment_service
from app.core.config import get_settings
from app.main import create_app


class FakePaymentService:
    async def create_checkout(self, *, user_id, product_type, plan):  # type: ignore[no-untyped-def]
        return {"checkout_url": "https://checkout.local", "status": "created"}

    async def get_subscription(self, user_id):  # type: ignore[no-untyped-def]
        return {"status": "free", "tier": None, "expires_at": None}

    async def cancel_subscription(self, user_id):  # type: ignore[no-untyped-def]
        return {"status": "canceled"}

    async def get_region_pricing(self, user_id):  # type: ignore[no-untyped-def]
        return {"region": "standard", "prices": {"monthly": 8.0, "quarterly": 20.0, "yearly": 70.0}}

    async def update_region(self, user_id, region):  # type: ignore[no-untyped-def]
        return {"region": region, "prices": {"monthly": 8.0, "quarterly": 20.0, "yearly": 70.0}}


class FakeWebhookSession:
    async def execute(self, stmt):  # type: ignore[no-untyped-def]
        class _R:
            def scalar_one_or_none(self):
                return None

        return _R()

    async def get(self, model, user_id):  # type: ignore[no-untyped-def]
        class U:
            def __init__(self, uid):
                self.id = uid
                self.subscription_status = "free"

        return U(user_id)

    def add(self, obj):  # type: ignore[no-untyped-def]
        return None

    async def commit(self):
        return None


def test_checkout_endpoint_returns_url() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: uuid4()
    app.dependency_overrides[get_payment_service] = lambda: FakePaymentService()
    client = TestClient(app)

    response = client.post("/api/v1/payments/checkout", json={"product_type": "subscription", "plan": "monthly"})
    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://checkout.local"


def test_webhook_invalid_signature_returns_401(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.post("/api/v1/payments/webhook/creem", json={"id": "evt_1", "data": {}}, headers={"X-Creem-Signature": "bad"})
    assert response.status_code == 401


def test_webhook_valid_signature_returns_ok(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    app = create_app()
    from app.db.session import get_db_session

    async def override_db():  # type: ignore[no-untyped-def]
        yield FakeWebhookSession()

    app.dependency_overrides[get_db_session] = override_db
    client = TestClient(app)
    payload = {"id": "evt_1", "type": "payment.succeeded", "data": {"user_id": str(uuid4()), "coin_amount": 0}}
    body = json.dumps(payload).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    response = client.post("/api/v1/payments/webhook/creem", data=body, headers={"X-Creem-Signature": signature, "Content-Type": "application/json"})
    assert response.status_code == 200
