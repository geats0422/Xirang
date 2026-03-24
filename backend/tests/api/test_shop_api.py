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
