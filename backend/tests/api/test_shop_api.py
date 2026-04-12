from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db.models.economy import ItemType, PurchaseStatus, QuotaType, TierRequired
from app.schemas.shop import (
    InventoryResponse,
    PurchaseRequest,
    ShopOfferResponse,
)
from app.services.shop.service import (
    InsufficientBalanceError,
    OfferNotActiveError,
    OfferNotFoundError,
    PurchaseLimitExceededError,
    ShopService,
)
from app.services.wallet.service import WalletService

pytestmark = pytest.mark.asyncio(loop_scope="module")


class FakeOffer:
    def __init__(self, offer_id, price=100, active=True, limit=None):
        self.id = offer_id
        self.item_code = "item_001"
        self.display_name = "Test Item"
        self.rarity = "common"
        self.price_asset_code = "COIN"
        self.price_amount = price
        self.is_active = active
        self.active_from = None
        self.active_to = None
        self.purchase_limit_per_user = limit
        self.quota_type = QuotaType.UNLIMITED
        self.max_capacity = None
        self.refill_days = None
        self.tier_required = TierRequired.FREE
        self.experiment_flag = None
        self.item_type = ItemType.TIME_TREASURE


class FakeInventory:
    def __init__(self, user_id, item_code, quantity=1):
        self.user_id = user_id
        self.item_code = item_code
        self.quantity = quantity
        self.updated_at = datetime.now(UTC)
        self.quota_max = None
        self.refill_days = None
        self.last_refill_at = None
        self.next_refill_at = None


class FakePurchase:
    def __init__(self, user_id, offer_id, item_code, price_asset_code, price_amount, status, **kw):
        self.id = uuid4()
        self.user_id = user_id
        self.offer_id = offer_id
        self.item_code = item_code
        self.price_asset_code = price_asset_code
        self.price_amount = price_amount
        self.status = status
        self.purchased_at = datetime.now(UTC)


class FakeShopRepo:
    def __init__(self):
        self.offers = {}
        self.inventories = {}
        self.purchases = {}
        self.counts = {}
        self.committed = False

    async def list_active_offers(self):
        return [o for o in self.offers.values() if o.is_active]

    async def get_offer(self, offer_id):
        return self.offers.get(offer_id)

    async def get_inventory(self, user_id):
        return [i for i in self.inventories.values() if i.user_id == user_id]

    async def upsert_inventory(
        self, user_id, item_code, quantity, quota_max=None, refill_days=None, is_auto_refill=False
    ):
        key = (user_id, item_code)
        if key in self.inventories:
            if is_auto_refill:
                self.inventories[key].quantity = quota_max if quota_max else quantity
            else:
                self.inventories[key].quantity += quantity
        else:
            self.inventories[key] = FakeInventory(user_id, item_code, quantity)
        return self.inventories[key]

    async def create_purchase_record(self, **kw):
        r = FakePurchase(**kw)
        self.purchases[kw.get("idempotency_key") or str(r.id)] = r
        if kw.get("offer_id"):
            k = (kw["user_id"], kw["offer_id"])
            self.counts[k] = self.counts.get(k, 0) + 1
        return r

    async def get_purchase_by_idempotency_key(self, key):
        return self.purchases.get(key)

    async def count_purchases_by_offer(self, user_id, offer_id):
        return self.counts.get((user_id, offer_id), 0)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


class FakeWalletService:
    def __init__(self, balance=500):
        self.balance = balance

    async def debit(self, **kw):
        if self.balance < kw["amount"]:
            raise InsufficientBalanceError("Insufficient")
        self.balance -= kw["amount"]
        return {"delta": -kw["amount"]}


@pytest.fixture
def shop_service():
    offer_id = uuid4()
    repo = FakeShopRepo()
    repo.offers[offer_id] = FakeOffer(offer_id)
    wallet = FakeWalletService()
    svc = ShopService(repository=repo, wallet_service=wallet)
    return svc, repo, wallet, offer_id


async def test_list_offers_returns_active(shop_service):
    service, repo, _, _ = shop_service
    inactive = uuid4()
    repo.offers[inactive] = FakeOffer(inactive, active=False)
    result = await service.list_offers()
    assert len(result) == 1
    assert isinstance(result[0], ShopOfferResponse)


async def test_purchase_succeeds(shop_service):
    service, repo, _, offer_id = shop_service
    user_id = uuid4()
    payload = PurchaseRequest(offer_id=offer_id)
    result = await service.purchase(user_id, payload)
    assert result.status == PurchaseStatus.COMPLETED
    assert repo.committed


async def test_purchase_insufficient_balance(shop_service):
    service, _repo, wallet, offer_id = shop_service
    wallet.balance = 50
    user_id = uuid4()
    payload = PurchaseRequest(offer_id=offer_id)
    with pytest.raises(InsufficientBalanceError):
        await service.purchase(user_id, payload)


async def test_purchase_nonexistent_offer(shop_service):
    service, _, _, _ = shop_service
    payload = PurchaseRequest(offer_id=uuid4())
    with pytest.raises(OfferNotFoundError):
        await service.purchase(uuid4(), payload)


async def test_purchase_inactive_offer(shop_service):
    service, repo, _, offer_id = shop_service
    repo.offers[offer_id].is_active = False
    payload = PurchaseRequest(offer_id=offer_id)
    with pytest.raises(OfferNotActiveError):
        await service.purchase(uuid4(), payload)


async def test_purchase_limit_exceeded(shop_service):
    service, repo, _, offer_id = shop_service
    repo.offers[offer_id].purchase_limit_per_user = 1
    user_id = uuid4()
    payload = PurchaseRequest(offer_id=offer_id)
    await service.purchase(user_id, payload)
    with pytest.raises(PurchaseLimitExceededError):
        await service.purchase(user_id, payload)


async def test_get_inventory_returns_items(shop_service):
    service, _repo, _, offer_id = shop_service
    user_id = uuid4()
    await service.purchase(user_id, PurchaseRequest(offer_id=offer_id))
    result = await service.get_inventory(user_id)
    assert isinstance(result, InventoryResponse)
    assert any(i.item_code == "item_001" for i in result.items)


class TestWalletServiceUnit:
    @pytest.fixture
    def wallet_repo(self):
        class Repo:
            def __init__(self, bal):
                self.bal = bal

            async def get_balance(self, uid, code):
                return self.bal

        return Repo(bal=750)

    async def test_get_balance_returns_sum(self, wallet_repo):
        service = WalletService(repository=wallet_repo)
        result = await service.get_balance(uuid4())
        assert result.balance == 750


class TestUseItemSchemas:
    def test_use_item_request_schema_valid(self):
        from app.schemas.shop import UseItemRequest

        req = UseItemRequest(item_code="xp_boost_2x", context={"run_id": "some-uuid"})
        assert req.item_code == "xp_boost_2x"
        assert req.context == {"run_id": "some-uuid"}

    def test_use_item_request_schema_defaults(self):
        from app.schemas.shop import UseItemRequest

        req = UseItemRequest(item_code="streak_freeze")
        assert req.context is None

    def test_use_item_response_schema(self):
        from app.schemas.shop import UseItemResponse

        resp = UseItemResponse(
            success=True,
            item_code="xp_boost_2x",
            quantity_remaining=2,
            effect_applied={"type": "xp_boost", "multiplier": 2.0},
        )
        assert resp.success is True
        assert resp.quantity_remaining == 2

    def test_active_effect_schema(self):
        from datetime import UTC, datetime

        from app.schemas.shop import ActiveEffect

        now = datetime.now(tz=UTC)
        eff = ActiveEffect(
            id=uuid4(),
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=now,
            source_item_code="xp_boost_2x",
            context=None,
            created_at=now,
        )
        assert eff.multiplier == 2.0
        assert eff.effect_type == "xp_boost"

    def test_active_effects_response_schema(self):
        from datetime import UTC, datetime

        from app.schemas.shop import ActiveEffect, ActiveEffectsResponse

        now = datetime.now(tz=UTC)
        eff = ActiveEffect(
            id=uuid4(),
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=now,
            source_item_code="xp_boost_2x",
            context=None,
            created_at=now,
        )
        resp = ActiveEffectsResponse(effects=[eff])
        assert len(resp.effects) == 1
        assert resp.effects[0].multiplier == 2.0


def get_current_user_id_for_test():
    from uuid import uuid4

    return uuid4()


class FakeEffectRepository:
    def __init__(self) -> None:
        self.effects: list = []
        self.use_records: list = []

    async def upsert_active_effect(self, **kw):
        from uuid import uuid4

        return uuid4()

    async def list_active_effects(self, user_id):
        return self.effects

    async def delete_expired_effects(self, user_id) -> None:
        pass

    async def update_expires(self, effect_id, expires_at) -> None:
        pass

    async def record_use(self, **kw):
        from uuid import uuid4

        return uuid4()


class FakeShopRepoForUseItem:
    def __init__(self) -> None:
        self.inventories: dict = {}

    async def get_inventory(self, user_id):
        return list(self.inventories.values())

    async def upsert_inventory(self, user_id, item_code, quantity, **kw):
        key = (user_id, item_code)
        if key in self.inventories:
            self.inventories[key].quantity += quantity
        else:
            inv = type(
                "Inv",
                (),
                {"user_id": user_id, "item_code": item_code, "quantity": quantity, "id": None},
            )()
            self.inventories[key] = inv
        return self.inventories[key]

    async def create_purchase_record(self, **kw):
        pass

    async def get_purchase_by_idempotency_key(self, key):
        return None

    async def count_purchases_by_offer(self, user_id, offer_id):
        return 0

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def list_active_offers(self):
        return []

    async def get_offer(self, offer_id):
        return None


class TestUseItemEndpoints:
    def test_use_item_endpoint_returns_200_with_fake_deps(self):
        from datetime import UTC, datetime
        from uuid import uuid4

        from fastapi.testclient import TestClient

        from app.main import create_app

        user_id = uuid4()

        fake_effect_repo = FakeEffectRepository()
        fake_effect_repo.effects = []

        inv_item = type(
            "Inv",
            (),
            {
                "user_id": user_id,
                "item_code": "xp_boost_2x",
                "quantity": 2,
                "id": uuid4(),
            },
        )()
        fake_shop_repo = FakeShopRepoForUseItem()
        fake_shop_repo.inventories[(user_id, "xp_boost_2x")] = inv_item

        class FakeShopServiceForUseItem:
            def __init__(self, repo, effect_repo) -> None:
                self._repo = repo
                self._effect_repo = effect_repo

            async def use_item(self, user_id, payload, effect_repo):
                from app.schemas.shop import UseItemResponse

                inventory = await self._repo.get_inventory(user_id)
                inv_item = next((i for i in inventory if i.item_code == payload.item_code), None)
                if not inv_item or inv_item.quantity < 1:
                    raise ValueError(
                        "INSUFFICIENT_INVENTORY: item not in inventory or quantity is 0"
                    )
                await self._repo.upsert_inventory(user_id, payload.item_code, -1)
                await effect_repo.record_use(user_id=user_id, item_code=payload.item_code)
                now = datetime.now(tz=UTC)
                new_expires = now.replace(second=0, microsecond=0)
                return UseItemResponse(
                    success=True,
                    item_code=payload.item_code,
                    quantity_remaining=1,
                    effect_applied={
                        "type": "xp_boost",
                        "multiplier": 2.0,
                        "expires_at": new_expires.isoformat(),
                    },
                )

            async def get_inventory(self, user_id):
                from app.schemas.shop import InventoryItemResponse, InventoryResponse

                items = await self._repo.get_inventory(user_id)
                return InventoryResponse(
                    items=[InventoryItemResponse.model_validate(i) for i in items]
                )

        app = create_app()
        from app.api.dependencies.auth import get_current_user_id
        from app.api.v1.shop import get_effect_repository, get_shop_service

        app.dependency_overrides[get_current_user_id] = lambda: user_id
        app.dependency_overrides[get_shop_service] = lambda: FakeShopServiceForUseItem(
            fake_shop_repo, fake_effect_repo
        )
        app.dependency_overrides[get_effect_repository] = lambda: fake_effect_repo

        client = TestClient(app)
        response = client.post(
            "/api/v1/shop/use-item",
            json={"item_code": "xp_boost_2x", "context": None},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["item_code"] == "xp_boost_2x"
        assert body["quantity_remaining"] == 1
        assert body["effect_applied"]["type"] == "xp_boost"
        assert body["effect_applied"]["multiplier"] == 2.0

    def test_active_effects_endpoint_returns_200_with_fake_deps(self):
        from datetime import UTC, datetime
        from uuid import uuid4

        from fastapi.testclient import TestClient

        from app.main import create_app

        user_id = uuid4()

        fake_effect_repo = FakeEffectRepository()
        now = datetime.now(tz=UTC)
        fake_effect_repo.effects = [
            type(
                "Eff",
                (),
                {
                    "id": uuid4(),
                    "effect_type": "xp_boost",
                    "multiplier": 2.0,
                    "expires_at": now,
                    "source_item_code": "xp_boost_2x",
                    "context": None,
                    "created_at": now,
                },
            )(),
        ]

        app = create_app()
        from app.api.dependencies.auth import get_current_user_id
        from app.api.v1.shop import get_effect_repository

        app.dependency_overrides[get_current_user_id] = lambda: user_id
        app.dependency_overrides[get_effect_repository] = lambda: fake_effect_repo

        client = TestClient(app)
        response = client.get("/api/v1/shop/active-effects")
        assert response.status_code == 200
        body = response.json()
        assert "effects" in body
        assert len(body["effects"]) == 1
        assert body["effects"][0]["effect_type"] == "xp_boost"
        assert body["effects"][0]["multiplier"] == 2.0
