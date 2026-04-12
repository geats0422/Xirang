from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="module")


class FakeEffectRecord:
    def __init__(
        self,
        id: UUID | None = None,
        user_id: UUID | None = None,
        effect_type: str = "",
        multiplier: float | None = None,
        expires_at: datetime | None = None,
        source_item_code: str | None = None,
        source_use_id: UUID | None = None,
        context: dict | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id or uuid4()
        self.user_id = user_id or uuid4()
        self.effect_type = effect_type
        self.multiplier = multiplier
        self.expires_at = expires_at
        self.source_item_code = source_item_code
        self.source_use_id = source_use_id
        self.context = context or {}
        self.created_at = created_at or datetime.now(UTC)


class FakeUseRecord:
    def __init__(
        self,
        id: UUID | None = None,
        user_id: UUID | None = None,
        item_code: str = "",
        inventory_id: UUID | None = None,
        effect_snapshot: dict | None = None,
        context: dict | None = None,
        used_at: datetime | None = None,
    ):
        self.id = id or uuid4()
        self.user_id = user_id or uuid4()
        self.item_code = item_code
        self.inventory_id = inventory_id
        self.effect_snapshot = effect_snapshot or {}
        self.context = context or {}
        self.used_at = used_at or datetime.now(UTC)


class FakeEffectRepository:
    def __init__(self) -> None:
        self.effects: dict[UUID, FakeEffectRecord] = {}
        self.use_records: dict[UUID, FakeUseRecord] = {}

    async def upsert_active_effect(
        self,
        *,
        user_id: UUID,
        effect_type: str,
        multiplier: float | None = None,
        expires_at: datetime | None = None,
        source_item_code: str | None = None,
        source_use_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> UUID:
        record = FakeEffectRecord(
            user_id=user_id,
            effect_type=effect_type,
            multiplier=multiplier,
            expires_at=expires_at,
            source_item_code=source_item_code,
            source_use_id=source_use_id,
            context=context,
        )
        self.effects[record.id] = record
        return record.id

    async def list_active_effects(self, user_id: UUID) -> list[FakeEffectRecord]:
        now = datetime.now(UTC)
        return [
            e
            for e in self.effects.values()
            if e.user_id == user_id and (e.expires_at is None or e.expires_at > now)
        ]

    async def delete_expired_effects(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        expired = [
            eid
            for eid, e in self.effects.items()
            if e.user_id == user_id and e.expires_at is not None and e.expires_at <= now
        ]
        for eid in expired:
            del self.effects[eid]

    async def update_expires(self, effect_id: UUID, expires_at: datetime) -> None:
        if effect_id in self.effects:
            self.effects[effect_id].expires_at = expires_at

    async def record_use(
        self,
        *,
        user_id: UUID,
        item_code: str,
        inventory_id: UUID | None = None,
        effect_snapshot: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> UUID:
        record = FakeUseRecord(
            user_id=user_id,
            item_code=item_code,
            inventory_id=inventory_id,
            effect_snapshot=effect_snapshot,
            context=context,
        )
        self.use_records[record.id] = record
        return record.id


class TestEffectRepositoryFake:
    async def test_upsert_returns_uuid(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        effect_id = await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
            source_item_code="xp_boost_2x",
        )
        assert effect_id is not None

    async def test_upsert_streak_freeze(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        effect_id = await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="streak_freeze",
            source_item_code="streak_freeze",
        )
        assert effect_id is not None

    async def test_list_active_effects_returns_effects(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
        )
        effects = await repo.list_active_effects(user_id)
        assert len(effects) >= 1
        assert effects[0].effect_type == "xp_boost"
        assert float(effects[0].multiplier) == 2.0

    async def test_list_active_effects_excludes_expired(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        effects = await repo.list_active_effects(user_id)
        assert not any(e.effect_type == "xp_boost" for e in effects)

    async def test_delete_expired_effects(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        await repo.delete_expired_effects(user_id)
        effects = await repo.list_active_effects(user_id)
        assert not any(e.effect_type == "xp_boost" for e in effects)

    async def test_record_use(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        record_id = await repo.record_use(
            user_id=user_id,
            item_code="xp_boost_2x",
            inventory_id=None,
            effect_snapshot={"type": "xp_boost", "multiplier": 2.0},
            context={"run_id": str(uuid4())},
        )
        assert record_id is not None

    async def test_update_expires(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        effect_id = await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        new_expires = datetime.now(UTC) + timedelta(minutes=15)
        await repo.update_expires(effect_id, new_expires)
        effects = await repo.list_active_effects(user_id)
        diff = abs((effects[0].expires_at - new_expires).total_seconds())
        assert diff < 5

    async def test_multiple_xp_boosts_same_type_stacks(self):
        repo = FakeEffectRepository()
        user_id = uuid4()
        id1 = await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        id2 = await repo.upsert_active_effect(
            user_id=user_id,
            effect_type="xp_boost",
            multiplier=2.0,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        assert id1 != id2
        effects = await repo.list_active_effects(user_id)
        xp_boosts = [e for e in effects if e.effect_type == "xp_boost"]
        assert len(xp_boosts) == 2
