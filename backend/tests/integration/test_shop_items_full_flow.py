from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.schemas.shop import UseItemRequest


@dataclass
class FakeEffect:
    id: UUID
    user_id: UUID
    effect_type: str
    multiplier: float | None
    expires_at: datetime | None
    source_item_code: str | None


class FakeEffectRepository:
    def __init__(self) -> None:
        self.effects: list[FakeEffect] = []

    async def upsert_active_effect(
        self,
        *,
        user_id: UUID,
        effect_type: str,
        multiplier: float | None = None,
        expires_at: datetime | None = None,
        source_item_code: str | None = None,
        source_use_id: UUID | None = None,
        context: dict | None = None,
    ) -> UUID:
        effect_id = uuid4()
        effect = FakeEffect(
            id=effect_id,
            user_id=user_id,
            effect_type=effect_type,
            multiplier=multiplier,
            expires_at=expires_at,
            source_item_code=source_item_code,
        )
        self.effects.append(effect)
        return effect_id

    async def list_active_effects(self, user_id: UUID) -> list[FakeEffect]:
        now = datetime.now(tz=UTC)
        return [
            e
            for e in self.effects
            if e.user_id == user_id and (e.expires_at is None or e.expires_at > now)
        ]

    async def delete_expired_effects(self, user_id: UUID) -> None:
        now = datetime.now(tz=UTC)
        self.effects = [
            e
            for e in self.effects
            if not (e.user_id == user_id and e.expires_at is not None and e.expires_at <= now)
        ]

    async def update_expires(self, effect_id: UUID, expires_at: datetime) -> None:
        for e in self.effects:
            if e.id == effect_id:
                e.expires_at = expires_at
                break

    async def record_use(
        self,
        *,
        user_id: UUID,
        item_code: str,
        inventory_id: UUID | None = None,
        effect_snapshot: dict | None = None,
        context: dict | None = None,
    ) -> UUID:
        return uuid4()


class TestShopItemsFullFlow:
    async def test_xp_boost_apply_creates_effect(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return [inv for inv in self.inventories.values() if inv.user_id == user_id]

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "xp_boost_2x")] = FakeInventoryItem(
            user_id, "xp_boost_2x", 2
        )

        payload = UseItemRequest(item_code="xp_boost_2x")
        result = await shop_svc.use_item(user_id, payload, effect_repo)

        assert result.success is True
        assert result.item_code == "xp_boost_2x"
        assert result.quantity_remaining == 1
        assert result.effect_applied is not None
        assert result.effect_applied["type"] == "xp_boost"
        assert result.effect_applied["multiplier"] == 2.0

        active_effects = await effect_repo.list_active_effects(user_id)
        assert len(active_effects) == 1
        assert active_effects[0].effect_type == "xp_boost"
        assert active_effects[0].multiplier == 2.0

    async def test_xp_boost_stacking_extends_duration(self):
        from app.services.shop.service import BOOST_DURATION_MINUTES, ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "xp_boost_2x")] = FakeInventoryItem(
            user_id, "xp_boost_2x", 5
        )

        payload = UseItemRequest(item_code="xp_boost_2x")

        result1 = await shop_svc.use_item(user_id, payload, effect_repo)
        first_expires = result1.effect_applied["expires_at"]
        first_expires_dt = datetime.fromisoformat(first_expires)

        result2 = await shop_svc.use_item(user_id, payload, effect_repo)
        second_expires = result2.effect_applied["expires_at"]
        second_expires_dt = datetime.fromisoformat(second_expires)

        assert second_expires_dt > first_expires_dt
        expected_delta = timedelta(minutes=BOOST_DURATION_MINUTES)
        actual_delta = second_expires_dt - first_expires_dt
        assert actual_delta == expected_delta

    async def test_time_treasure_requires_active_boost(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "time_treasure")] = FakeInventoryItem(
            user_id, "time_treasure", 3
        )

        payload = UseItemRequest(item_code="time_treasure")
        with pytest.raises(ValueError, match="NO_ACTIVE_BOOST"):
            await shop_svc.use_item(user_id, payload, effect_repo)

    async def test_revive_creates_shield_effect_with_180_seconds(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "revival")] = FakeInventoryItem(user_id, "revival", 1)

        payload = UseItemRequest(item_code="revival")
        result = await shop_svc.use_item(user_id, payload, effect_repo)

        assert result.success is True
        assert result.effect_applied["type"] == "revive_shield"
        assert result.effect_applied["shield_seconds"] == 180

        active_effects = await effect_repo.list_active_effects(user_id)
        revive_shields = [e for e in active_effects if e.effect_type == "revive_shield"]
        assert len(revive_shields) == 1

    async def test_streak_freeze_creates_no_expiry_effect(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "streak_freeze")] = FakeInventoryItem(
            user_id, "streak_freeze", 1
        )

        payload = UseItemRequest(item_code="streak_freeze")
        result = await shop_svc.use_item(user_id, payload, effect_repo)

        assert result.success is True
        assert result.effect_applied["type"] == "streak_freeze"

        active_effects = await effect_repo.list_active_effects(user_id)
        streak_freeze_effects = [e for e in active_effects if e.effect_type == "streak_freeze"]
        assert len(streak_freeze_effects) == 1
        assert streak_freeze_effects[0].expires_at is None

    async def test_inventory_decremented_after_each_use(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "xp_boost_2x")] = FakeInventoryItem(
            user_id, "xp_boost_2x", 3
        )

        payload = UseItemRequest(item_code="xp_boost_2x")

        result = await shop_svc.use_item(user_id, payload, effect_repo)
        assert result.quantity_remaining == 2

        result2 = await shop_svc.use_item(user_id, payload, effect_repo)
        assert result2.quantity_remaining == 1

        result3 = await shop_svc.use_item(user_id, payload, effect_repo)
        assert result3.quantity_remaining == 0

    async def test_use_item_insufficient_inventory_raises_error(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "xp_boost_2x")] = FakeInventoryItem(
            user_id, "xp_boost_2x", 0
        )

        payload = UseItemRequest(item_code="xp_boost_2x")
        with pytest.raises(ValueError, match="INSUFFICIENT_INVENTORY"):
            await shop_svc.use_item(user_id, payload, effect_repo)

    async def test_unknown_item_code_raises_error(self):
        from app.services.shop.service import ShopService

        user_id = uuid4()
        effect_repo = FakeEffectRepository()

        @dataclass
        class FakeInventoryItem:
            user_id: UUID
            item_code: str
            quantity: int

        class FakeShopRepo:
            def __init__(self) -> None:
                self.inventories: dict[tuple[UUID, str], FakeInventoryItem] = {}

            async def get_inventory(self, user_id):
                return list(self.inventories.values())

            async def upsert_inventory(self, user_id, item_code, quantity, **kw):
                key = (user_id, item_code)
                if key in self.inventories:
                    self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventoryItem(user_id, item_code, quantity)
                return self.inventories[key]

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

            async def list_active_offers(self):
                return []

            async def get_offer(self, offer_id):
                return None

            async def create_purchase_record(self, **kw):
                pass

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

        class FakeWalletService:
            pass

        shop_repo = FakeShopRepo()
        wallet_svc = FakeWalletService()
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        shop_repo.inventories[(user_id, "nonexistent_item")] = FakeInventoryItem(
            user_id, "nonexistent_item", 5
        )

        payload = UseItemRequest(item_code="nonexistent_item")
        with pytest.raises(ValueError, match="ITEM_NOT_USABLE"):
            await shop_svc.use_item(user_id, payload, effect_repo)
