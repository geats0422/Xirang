from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1 import shop as shop_router
from app.db.models.economy import PurchaseStatus
from app.main import create_app
from app.schemas.shop import PurchaseRequest, PurchaseResponse, ShopOfferResponse


@dataclass
class FakeLedgerEntry:
    id: UUID
    asset_code: str
    delta: int
    balance_after: int
    reason_code: str
    source_type: str | None
    source_id: UUID | None
    created_at: datetime


class FakeShopService:
    def __init__(self) -> None:
        self.offer_id = uuid4()

    async def list_offers(self) -> list[ShopOfferResponse]:
        return [
            ShopOfferResponse(
                id=self.offer_id,
                item_code="item_001",
                display_name="XP Boost Potion",
                rarity="uncommon",
                price_asset_code="COIN",
                price_amount=200,
                is_active=True,
                active_from=None,
                active_to=None,
                purchase_limit_per_user=None,
                quota_type="unlimited",
                max_capacity=None,
                refill_days=None,
                tier_required="free",
                experiment_flag=None,
                item_type="time_treasure",
            )
        ]

    async def list_offers_for_user(
        self, user_tier: str = "free", active_experiment_flags: list[str] | None = None
    ) -> list[ShopOfferResponse]:
        return await self.list_offers()

    async def purchase(self, user_id: UUID, payload: PurchaseRequest) -> PurchaseResponse:
        return PurchaseResponse(
            id=uuid4(),
            user_id=user_id,
            offer_id=payload.offer_id,
            item_code="item_001",
            price_asset_code="COIN",
            price_amount=200,
            status=PurchaseStatus.COMPLETED,
            purchased_at=datetime.now(UTC),
        )

    async def get_inventory(self, user_id: UUID):
        return type(
            "InventoryResponse",
            (),
            {
                "model_dump": lambda self, mode="json": {
                    "items": [
                        {
                            "user_id": str(user_id),
                            "item_code": "item_001",
                            "quantity": 1,
                            "updated_at": datetime.now(UTC).isoformat(),
                        }
                    ]
                }
            },
        )()


class FakeWalletService:
    async def get_balance(self, user_id: UUID, asset_code: str = "COIN"):
        return type(
            "BalanceResponse",
            (),
            {"model_dump": lambda self, mode="json": {"asset_code": asset_code, "balance": 500}},
        )()


class FakeWalletRepository:
    async def list_ledger(
        self, *, user_id: UUID, asset_code: str = "COIN"
    ) -> list[FakeLedgerEntry]:
        return [
            FakeLedgerEntry(
                id=uuid4(),
                asset_code=asset_code,
                delta=50,
                balance_after=500,
                reason_code="run_settlement",
                source_type="run",
                source_id=uuid4(),
                created_at=datetime.now(UTC),
            )
        ]


def create_test_client(user_id: UUID) -> tuple[TestClient, FakeShopService]:
    app = create_app()
    fake_shop = FakeShopService()
    app.dependency_overrides[shop_router.get_current_user_id] = lambda: user_id
    app.dependency_overrides[shop_router.get_shop_service] = lambda: fake_shop
    app.dependency_overrides[shop_router.get_wallet_service] = lambda: FakeWalletService()
    app.dependency_overrides[shop_router.get_wallet_repository] = lambda: FakeWalletRepository()
    return TestClient(app), fake_shop


def test_shop_items_endpoint_returns_offer_list() -> None:
    client, _ = create_test_client(uuid4())

    response = client.get("/api/v1/shop/items")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["item_code"] == "item_001"


def test_shop_purchase_endpoint_returns_purchase_record() -> None:
    user_id = uuid4()
    client, fake_shop = create_test_client(user_id)

    response = client.post(
        "/api/v1/shop/purchase",
        json={"offer_id": str(fake_shop.offer_id), "idempotency_key": "req-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["user_id"] == str(user_id)


def test_shop_balance_and_ledger_endpoints_return_wallet_data() -> None:
    client, _ = create_test_client(uuid4())

    balance_response = client.get("/api/v1/shop/balance")
    ledger_response = client.get("/api/v1/shop/ledger")

    assert balance_response.status_code == 200
    assert balance_response.json()["balance"] == 500

    assert ledger_response.status_code == 200
    assert len(ledger_response.json()) == 1
    assert ledger_response.json()[0]["reason_code"] == "run_settlement"
