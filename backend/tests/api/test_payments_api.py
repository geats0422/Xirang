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
    def __init__(self) -> None:
        self.user = None

    async def execute(self, stmt):  # type: ignore[no-untyped-def]
        _ = stmt

        class _R:
            def scalar_one_or_none(self):
                return None

        return _R()

    async def get(self, model, user_id):  # type: ignore[no-untyped-def]
        _ = model

        class U:
            def __init__(self, uid):
                self.id = uid
                self.subscription_status = "free"
                self.subscription_tier = None
                self.subscription_expires_at = None
                self.creem_customer_id = None
                self.creem_subscription_id = None

        self.user = U(user_id)
        return self.user

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


def test_webhook_missing_secret_returns_503(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/payments/webhook/creem",
        json={"id": "evt_1", "eventType": "subscription.paid", "object": {}},
        headers={"Creem-Signature": "anything"},
    )

    assert response.status_code == 503


def test_webhook_invalid_json_returns_400(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    body = b"not-json"
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/payments/webhook/creem",
        data=body,
        headers={"Creem-Signature": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 400


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


def test_webhook_subscription_paid_updates_user_from_creem_event(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("CREEM_PRODUCT_SUB_MONTHLY", "prod_monthly")
    get_settings.cache_clear()
    app = create_app()
    from app.db.session import get_db_session

    webhook_session = FakeWebhookSession()

    async def override_db():  # type: ignore[no-untyped-def]
        yield webhook_session

    app.dependency_overrides[get_db_session] = override_db
    client = TestClient(app)
    user_id = uuid4()
    payload = {
        "id": "evt_subscription_paid",
        "eventType": "subscription.paid",
        "object": {
            "id": "sub_123",
            "status": "active",
            "current_period_end_date": "2026-06-16T11:58:38.000Z",
            "metadata": {"user_id": str(user_id), "plan": "monthly", "product_type": "subscription"},
            "customer": {"id": "cust_123"},
            "product": {"id": "prod_monthly", "price": 960, "currency": "USD"},
        },
    }
    body = json.dumps(payload).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/payments/webhook/creem",
        data=body,
        headers={"Creem-Signature": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert webhook_session.user.subscription_status == "active"
    assert webhook_session.user.subscription_tier == "monthly"
    assert webhook_session.user.creem_customer_id == "cust_123"
    assert webhook_session.user.creem_subscription_id == "sub_123"


def test_webhook_subscription_paid_ignores_unconfigured_product(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("CREEM_PRODUCT_SUB_MONTHLY", "prod_monthly")
    get_settings.cache_clear()
    app = create_app()
    from app.db.session import get_db_session

    webhook_session = FakeWebhookSession()

    async def override_db():  # type: ignore[no-untyped-def]
        yield webhook_session

    app.dependency_overrides[get_db_session] = override_db
    client = TestClient(app)
    user_id = uuid4()
    payload = {
        "id": "evt_wrong_product",
        "eventType": "subscription.paid",
        "object": {
            "id": "sub_123",
            "status": "active",
            "metadata": {"user_id": str(user_id), "plan": "monthly", "product_type": "subscription"},
            "customer": {"id": "cust_123"},
            "product": {"id": "prod_attacker", "price": 960, "currency": "USD"},
        },
    }
    body = json.dumps(payload).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/payments/webhook/creem",
        data=body,
        headers={"Creem-Signature": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert webhook_session.user.subscription_status == "free"


def test_webhook_subscription_paused_revokes_access(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("CREEM_PRODUCT_SUB_MONTHLY", "prod_monthly")
    get_settings.cache_clear()
    app = create_app()
    from app.db.session import get_db_session

    webhook_session = FakeWebhookSession()

    async def override_db():  # type: ignore[no-untyped-def]
        yield webhook_session

    app.dependency_overrides[get_db_session] = override_db
    client = TestClient(app)
    user_id = uuid4()
    payload = {
        "id": "evt_subscription_paused",
        "eventType": "subscription.paused",
        "object": {
            "id": "sub_123",
            "metadata": {"user_id": str(user_id), "plan": "monthly", "product_type": "subscription"},
            "product": {"id": "prod_monthly", "price": 960, "currency": "USD"},
        },
    }
    body = json.dumps(payload).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/payments/webhook/creem",
        data=body,
        headers={"Creem-Signature": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert webhook_session.user.subscription_status == "paused"


def test_webhook_invalid_user_id_is_ignored(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CREEM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("CREEM_PRODUCT_SUB_MONTHLY", "prod_monthly")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    payload = {
        "id": "evt_bad_user",
        "eventType": "subscription.paid",
        "object": {
            "id": "sub_123",
            "metadata": {"user_id": "not-a-uuid", "plan": "monthly"},
            "product": {"id": "prod_monthly"},
        },
    }
    body = json.dumps(payload).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/payments/webhook/creem",
        data=body,
        headers={"Creem-Signature": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json()["ignored"] is True
