# Shops 道具系统实现计划

**目标：** 补齐 5 类道具（连胜激冻、经验值翻倍、时间宝、复活币、金币包充值）的完整购买→库存→使用→生效链路，前后端全链路联通。

**架构概述：** 采用"混合模型"：金币包即时充值到账，其余道具先入背包再在对应场景消耗使用。后端以现有 wallet/ledger/inventory 账本体系为基础，新增 `active_effects` 和 `use_records` 两张表承载生效状态，前端重构 ShopPage 为组件化架构并新增弹窗系统。

**技术栈：** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL / Vue 3 + TypeScript + Vitest + Vite

**设计规格：** `docs/specs/2026-04-08-shop-items-design.md`

---

## 依赖关系

```
[T1 DB迁移] → [T2 后端 schemas/service/repository 基础]
                        ↓
              [T3 active_effects + use_records 表/Repo]
                        ↓
              [T4 use-item API 端点]
                        ↓
              [T5 经验翻倍生效逻辑（settlement 计算改写）]
                        ↓
              [T6 revive 改造（库存优先 + 180s 护盾）]
                        ↓
              [T7 前端 shop.ts API 扩展]
                        ↓
              [T8 useInventory / useActiveEffects composables]
                        ↓
              [T9 道具卡片组件 + ShopHeader + 激活增益条]
                        ↓
              [T10 充值弹窗 + 道具使用确认弹窗 + 时间宝提示弹窗]
                        ↓
              [T11 AbyssReviveModal（从 EndlessAbyssPage 提取）]
                        ↓
              [T12 ShopPage 重构（整合所有组件）]
                        ↓
              [T13 端到端集成测试]
```

---

## 任务清单

### Task 1: DB 迁移 — 新增 active_effects 和 use_records 表

**Files:**
- Create: `backend/alembic/versions/YYYYMMDD_HHMMSS_add_shop_effects_tables.py`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/db/test_models_phase1.py（追加）
async def test_active_effects_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'active_effects')")
    )
    assert result.scalar()

async def test_use_records_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'use_records')")
    )
    assert result.scalar()
```
Run: `uv run pytest tests/db/test_models_phase1.py::test_active_effects_table_exists -v`
Expected: FAIL（表不存在）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Write migration**
```python
# backend/alembic/versions/xxxx_add_shop_effects_tables.py
"""add shop effects tables

Revision ID: xxxx
Revises: 5f1feb885f66
"""
from alembic import op
import sqlalchemy as sa

revision = "xxxx"
down_revision = "5f1feb885f66"

def upgrade() -> None:
    op.create_table(
        "active_effects",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("effect_type", sa.String(40), nullable=False),
        sa.Column("multiplier", sa.Numeric(5, 2), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_item_code", sa.String(80), nullable=True),
        sa.Column("source_use_id", sa.UUID(), nullable=True),
        sa.Column("context", sa.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_active_effects_user_expires", "active_effects", ["user_id", "expires_at"])
    op.create_index("ix_active_effects_user_type", "active_effects", ["user_id", "effect_type"])

    op.create_table(
        "use_records",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_code", sa.String(80), nullable=False),
        sa.Column("inventory_id", sa.UUID(), sa.ForeignKey("inventories.id"), nullable=True),
        sa.Column("effect_snapshot", sa.JSONB, nullable=True),
        sa.Column("context", sa.JSONB, nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_use_records_user", "use_records", ["user_id", "used_at"])

def downgrade() -> None:
    op.drop_table("use_records")
    op.drop_table("active_effects")
```

**Step 4 — Apply migration and verify**
Run: `cd backend && uv run alembic upgrade head`
Run: `uv run pytest tests/db/test_models_phase1.py::test_active_effects_table_exists -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/alembic/versions/xxxx_add_shop_effects_tables.py
git commit -m "feat(shop): add active_effects and use_records tables"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app alembic/versions/xxxx_add_shop_effects_tables.py`

---

### Task 2: 后端 schemas — 新增 UseItemRequest / UseItemResponse / ActiveEffect / ActiveEffectsResponse

**Files:**
- Modify: `backend/app/schemas/shop.py`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/api/test_shop_api.py（追加）
async def test_use_item_request_schema_valid():
    from app.schemas.shop import UseItemRequest
    req = UseItemRequest(item_code="xp_boost_2x", context={"run_id": "some-uuid"})
    assert req.item_code == "xp_boost_2x"
    assert req.context == {"run_id": "some-uuid"}

async def test_active_effects_response_schema():
    from app.schemas.shop import ActiveEffect, ActiveEffectsResponse
    from datetime import datetime, timezone
    eff = ActiveEffect(
        id="uuid-here",
        effect_type="xp_boost",
        multiplier=2.0,
        expires_at=datetime.now(tz=timezone.utc),
        source_item_code="xp_boost_2x"
    )
    resp = ActiveEffectsResponse(effects=[eff])
    assert len(resp.effects) == 1
    assert resp.effects[0].multiplier == 2.0
```
Run: `uv run pytest tests/api/test_shop_api.py -k "use_item_request_schema_valid or active_effects_response_schema" -v`
Expected: FAIL（ImportError / NameError）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Add schemas**
```python
# backend/app/schemas/shop.py（追加）
class UseItemRequest(BaseModel):
    item_code: str
    context: dict | None = None

class UseItemResponse(BaseModel):
    success: bool
    item_code: str
    quantity_remaining: int
    effect_applied: dict | None = None

class ActiveEffect(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    effect_type: str
    multiplier: float | None = None
    expires_at: datetime | None = None
    source_item_code: str | None = None
    context: dict | None = None
    created_at: datetime

class ActiveEffectsResponse(BaseModel):
    effects: list[ActiveEffect]
```

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/api/test_shop_api.py -k "use_item_request_schema_valid or active_effects_response_schema" -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/app/schemas/shop.py
git commit -m "feat(shop): add use-item and active-effects schemas"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app/schemas/shop.py && uv run mypy app/schemas/shop.py`

---

### Task 3: 后端 repository — 新增 ActiveEffectRepository / UseRecordRepository

**Files:**
- Create: `backend/app/repositories/effect_repository.py`
- Modify: `backend/app/repositories/shop_repository.py`（如需注册到 DI）

**Step 1 — Write failing test (RED)**
```python
# backend/tests/repositories/test_effect_repository.py
import pytest
from uuid import uuid4

async def test_upsert_active_effect(db_session):
    from app.repositories.effect_repository import EffectRepository
    repo = EffectRepository(db_session)
    effect_id = await repo.upsert_active_effect(
        user_id=uuid4(),
        effect_type="xp_boost",
        multiplier=2.0,
        expires_at=None,
        source_item_code="xp_boost_2x",
    )
    assert effect_id is not None

async def test_list_active_effects(db_session):
    from app.repositories.effect_repository import EffectRepository
    repo = EffectRepository(db_session)
    user_id = uuid4()
    await repo.upsert_active_effect(user_id=user_id, effect_type="xp_boost", multiplier=2.0)
    effects = await repo.list_active_effects(user_id)
    assert len(effects) >= 1
```
Run: `uv run pytest tests/repositories/test_effect_repository.py -v`
Expected: FAIL（模块不存在）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Write repository**
```python
# backend/app/repositories/effect_repository.py
from __future__ import annotations
from datetime import UTC, datetime
from uuid import UUID
from typing import Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.common import UUIDPrimaryKeyMixin, TimestampMixin
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ActiveEffectModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "active_effects"
    user_id: Any
    effect_type: Any
    multiplier: Any
    expires_at: Any
    source_item_code: Any
    source_use_id: Any
    context: Any

class UseRecordModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "use_records"
    user_id: Any
    item_code: Any
    inventory_id: Any
    effect_snapshot: Any
    context: Any
    used_at: Any

class EffectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        # For xp_boost: replace existing same-type effect (upsert)
        # For revive_shield: append new record
        model = ActiveEffectModel(
            id=UUID() if False else None,  # use server default
            user_id=user_id,
            effect_type=effect_type,
            multiplier=multiplier,
            expires_at=expires_at,
            source_item_code=source_item_code,
            source_use_id=source_use_id,
            context=context,
        )
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def list_active_effects(self, user_id: UUID) -> list[ActiveEffectModel]:
        now = datetime.now(tz=UTC)
        result = await self._session.execute(
            select(ActiveEffectModel)
            .where(ActiveEffectModel.user_id == user_id)
            .where(
                (ActiveEffectModel.expires_at == None) |
                (ActiveEffectModel.expires_at > now)
            )
        )
        return list(result.scalars().all())

    async def delete_expired_effects(self, user_id: UUID) -> None:
        now = datetime.now(tz=UTC)
        await self._session.execute(
            delete(ActiveEffectModel)
            .where(ActiveEffectModel.user_id == user_id)
            .where(ActiveEffectModel.expires_at != None)
            .where(ActiveEffectModel.expires_at <= now)
        )

    async def record_use(
        self,
        *,
        user_id: UUID,
        item_code: str,
        inventory_id: UUID | None = None,
        effect_snapshot: dict | None = None,
        context: dict | None = None,
    ) -> UUID:
        model = UseRecordModel(
            id=UUID() if False else None,
            user_id=user_id,
            item_code=item_code,
            inventory_id=inventory_id,
            effect_snapshot=effect_snapshot,
            context=context,
            used_at=datetime.now(tz=UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.id
```

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/repositories/test_effect_repository.py -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/app/repositories/effect_repository.py
git commit -m "feat(shop): add EffectRepository for active_effects and use_records"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app/repositories/effect_repository.py && uv run mypy app/repositories/effect_repository.py`

---

### Task 4: 后端 API — 新增 POST /api/v1/shop/use-item 和 GET /api/v1/shop/active-effects

**Files:**
- Modify: `backend/app/api/v1/shop.py`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/api/test_shop_api.py（追加）
async def test_use_item_endpoint_xp_boost(test_client, fake_auth, db_session):
    # 先购买一个 xp_boost
    # 再调用 use-item
    response = test_client.post(
        "/api/v1/shop/use-item",
        json={"item_code": "xp_boost_2x"},
        headers=fake_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["effect_applied"]["type"] == "xp_boost"
    assert body["effect_applied"]["multiplier"] == 2.0

async def test_active_effects_endpoint(test_client, fake_auth):
    response = test_client.get("/api/v1/shop/active-effects", headers=fake_auth)
    assert response.status_code == 200
    assert "effects" in response.json()
```
Run: `uv run pytest tests/api/test_shop_api.py -k "use_item_endpoint or active_effects_endpoint" -v`
Expected: FAIL（404）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Add endpoints**
```python
# backend/app/api/v1/shop.py（追加）
from app.schemas.shop import UseItemRequest, UseItemResponse, ActiveEffectsResponse

async def get_effect_repository(session: AsyncSession = Depends(get_db_session)):
    from app.repositories.effect_repository import EffectRepository
    return EffectRepository(session)

@router.post("/use-item", response_model=UseItemResponse)
async def use_item(
    request: UseItemRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: ShopService = Depends(get_shop_service),
    effect_repo: EffectRepository = Depends(get_effect_repository),
) -> UseItemResponse:
    try:
        result = await service.use_item(user_id, request, effect_repo)
        return result
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

@router.get("/active-effects", response_model=ActiveEffectsResponse)
async def get_active_effects(
    user_id: UUID = Depends(get_current_user_id),
    effect_repo: EffectRepository = Depends(get_effect_repository),
) -> ActiveEffectsResponse:
    await effect_repo.delete_expired_effects(user_id)
    effects = await effect_repo.list_active_effects(user_id)
    return ActiveEffectsResponse(effects=[ActiveEffect.model_validate(e) for e in effects])
```

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/api/test_shop_api.py -k "use_item_endpoint or active_effects_endpoint" -v`
Expected: PASS（路由存在，business logic 由 Task 5 提供）

**Step 5 — Commit**
```bash
git add backend/app/api/v1/shop.py
git commit -m "feat(shop): add use-item and active-effects API endpoints"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app/api/v1/shop.py && uv run mypy app/api/v1/shop.py`

---

### Task 5: 后端 service — ShopService.use_item() 实现（经验翻倍、时长叠加、时间宝）

**Files:**
- Modify: `backend/app/services/shop/service.py`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/services/test_shop_service.py（追加）
async def test_use_item_xp_boost_extends_duration(shop_service, effect_repo, user_id):
    # 先使用一个 xp_boost_2x -> 10min
    result1 = await shop_service.use_item(user_id, UseItemRequest(item_code="xp_boost_2x"), effect_repo)
    assert result1.effect_applied["multiplier"] == 2.0
    first_expires = result1.effect_applied["expires_at"]

    # 再使用一个 xp_boost_2x -> +10min
    result2 = await shop_service.use_item(user_id, UseItemRequest(item_code="xp_boost_2x"), effect_repo)
    assert result2.effect_applied["expires_at"] > first_expires  # 时长叠加

async def test_use_item_time_treasure_without_boost_fails(shop_service, effect_repo, user_id):
    with pytest.raises(ValueError, match="NO_ACTIVE_BOOST"):
        await shop_service.use_item(user_id, UseItemRequest(item_code="time_treasure"), effect_repo)
```
Run: `uv run pytest tests/services/test_shop_service.py -k "xp_boost_extends or time_treasure_without" -v`
Expected: FAIL（use_item 方法不存在）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Implement use_item in ShopService**
```python
# backend/app/services/shop/service.py
from datetime import UTC, datetime, timedelta

BOOST_DURATION_MINUTES = 10
BOOST_MULTIPLIERS = {"xp_boost_1_5x": 1.5, "xp_boost_2x": 2.0, "xp_boost_3x": 3.0}
TIME_TREASURE_DURATION_MINUTES = 10

class ShopService:
    async def use_item(
        self,
        user_id: UUID,
        payload: UseItemRequest,
        effect_repo: EffectRepository,
    ) -> UseItemResponse:
        # 1. 扣减库存
        inventory = await self.repository.get_inventory(user_id)
        inv_item = next((i for i in inventory if i.item_code == payload.item_code), None)
        if not inv_item or inv_item.quantity < 1:
            raise ValueError("INSUFFICIENT_INVENTORY: item not in inventory or quantity is 0")

        # 2. 扣1个库存
        await self.repository.upsert_inventory(user_id, payload.item_code, -1)

        # 3. 记录使用
        use_record_id = await effect_repo.record_use(
            user_id=user_id,
            item_code=payload.item_code,
            inventory_id=inv_item.id if hasattr(inv_item, "id") else None,
            context=payload.context,
        )

        # 4. 触发效果
        effect = self._apply_item_effect(user_id, payload.item_code, use_record_id, effect_repo)
        remaining = await self.repository.get_inventory(user_id)
        remaining_qty = next((i.quantity for i in remaining if i.item_code == payload.item_code), 0)

        return UseItemResponse(
            success=True,
            item_code=payload.item_code,
            quantity_remaining=remaining_qty,
            effect_applied=effect,
        )

    def _apply_item_effect(
        self,
        user_id: UUID,
        item_code: str,
        use_record_id: UUID,
        effect_repo: EffectRepository,
    ) -> dict:
        now = datetime.now(tz=UTC)
        if item_code in BOOST_MULTIPLIERS:
            multiplier = BOOST_MULTIPLIERS[item_code]
            # 查当前同倍率有效效果
            active = [e for e in effect_repo.blocking_list_active_effects(user_id) if e.effect_type == "xp_boost" and e.multiplier == multiplier]
            if active:
                # 延长时间
                new_expires = (active[0].expires_at or now) + timedelta(minutes=BOOST_DURATION_MINUTES)
            else:
                # 新建
                new_expires = now + timedelta(minutes=BOOST_DURATION_MINUTES)
            effect_id = effect_repo.upsert_active_effect(
                user_id=user_id,
                effect_type="xp_boost",
                multiplier=multiplier,
                expires_at=new_expires,
                source_item_code=item_code,
                source_use_id=use_record_id,
            )
            return {"type": "xp_boost", "multiplier": multiplier, "expires_at": new_expires.isoformat()}

        elif item_code == "time_treasure":
            active = [e for e in effect_repo.blocking_list_active_effects(user_id) if e.effect_type == "xp_boost"]
            if not active:
                raise ValueError("NO_ACTIVE_BOOST: no active xp boost to extend")
            active[0].expires_at = active[0].expires_at + timedelta(minutes=TIME_TREASURE_DURATION_MINUTES)
            effect_repo.update_expires(active[0].id, active[0].expires_at)
            return {"type": "time_treasure", "extended_by_minutes": TIME_TREASURE_DURATION_MINUTES, "new_expires_at": active[0].expires_at.isoformat()}

        elif item_code == "streak_freeze":
            effect_repo.upsert_active_effect(user_id=user_id, effect_type="streak_freeze", source_item_code=item_code, source_use_id=use_record_id)
            return {"type": "streak_freeze"}

        elif item_code == "revival":
            effect_repo.upsert_active_effect(
                user_id=user_id,
                effect_type="revive_shield",
                expires_at=now + timedelta(seconds=180),
                source_item_code=item_code,
                source_use_id=use_record_id,
                context={"run_id": payload.context.get("run_id") if payload.context else None},
            )
            return {"type": "revive_shield", "shield_seconds": 180}

        else:
            raise ValueError(f"ITEM_NOT_USABLE: unknown item_code {item_code}")
```

> 注：`blocking_list_active_effects` 和 `update_expires` 为 EffectRepository 新增的同步包装方法（用于在 async context 中调用）。

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/services/test_shop_service.py -k "xp_boost_extends or time_treasure_without" -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/app/services/shop/service.py
git commit -m "feat(shop): implement use_item with xp boost stacking and time treasure"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app/services/shop/service.py && uv run mypy app/services/shop/service.py`

---

### Task 6: 后端 settlement — 经验翻倍在结算时生效

**Files:**
- Modify: `backend/app/services/runs/service.py`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/services/test_run_service.py（追加）
async def test_settlement_xp_is_multiplied_by_active_boost(db_session, user_id):
    # 1. 激活 xp_boost_2x
    effect_repo = EffectRepository(db_session)
    await effect_repo.upsert_active_effect(user_id=user_id, effect_type="xp_boost", multiplier=2.0)
    # 2. 结算（基础 XP=100）
    xp = await run_service._calculate_settlement_xp(user_id=user_id, base_xp=100)
    assert xp == 200  # 2x multiplier

async def test_settlement_xp_no_boost_no_change(db_session, user_id):
    xp = await run_service._calculate_settlement_xp(user_id=user_id, base_xp=100)
    assert xp == 100
```
Run: `uv run pytest tests/services/test_run_service.py -k "settlement_xp_is_multiplied" -v`
Expected: FAIL（方法不存在）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Add settlement multiplier logic**
```python
# backend/app/services/runs/service.py
# 在 _build_settlement 或新建 _calculate_settlement_xp 方法中：
async def _calculate_settlement_xp(self, user_id: UUID, base_xp: int) -> int:
    from app.repositories.effect_repository import EffectRepository
    effect_repo = EffectRepository(self._repository._session)
    now = datetime.now(tz=UTC)
    active = await effect_repo.list_active_effects(user_id)
    xp_boosts = [e for e in active if e.effect_type == "xp_boost" and (e.expires_at is None or e.expires_at > now)]
    if xp_boosts:
        max_mult = max((float(e.multiplier or 1.0) for e in xp_boosts), default=1.0)
        return int(base_xp * max_mult)
    return base_xp
```

然后在 `_build_settlement()` 调用处将 `xp_gained = await self._calculate_settlement_xp(...)` 替换原有值。

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/services/test_run_service.py -k "settlement_xp_is_multiplied" -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/app/services/runs/service.py
git commit -m "feat(shop): apply xp boost multiplier during settlement calculation"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app/services/runs/service.py && uv run mypy app/services/runs/service.py`

---

### Task 7: 后端 revive 改造 — 库存优先 + 180s 护盾

**Files:**
- Modify: `backend/app/services/runs/service.py`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/services/test_run_service.py（追加）
async def test_revive_prefers_inventory_revival(db_session, user_id, run_id):
    # 库存有 revival > 0
    await shop_repo.upsert_inventory(user_id, "revival", 2)
    revived = await run_service.revive(user_id, run_id)
    # 应该不扣 COIN，HP 恢复，护盾 180s
    assert revived["shield_seconds"] == 180
    assert revived["hp_restored"] == 1

async def test_revive_falls_back_to_coins_when_no_inventory(db_session, user_id, run_id):
    # 库存 revival = 0，COIN 充足
    revived = await run_service.revive(user_id, run_id)
    assert revived["shield_seconds"] == 180
```
Run: `uv run pytest tests/services/test_run_service.py -k "revive_prefers_inventory or revive_falls_back" -v`
Expected: FAIL

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Rewrite revive logic**
```python
# backend/app/services/runs/service.py
REVIVE_SHIELD_SECONDS = 180  # 3 minutes (was 60)

async def revive(self, user_id: UUID, run_id: UUID) -> dict:
    # 1. Check inventory for revival items
    inventory = await self.repository.get_inventory(user_id)
    inv_item = next((i for i in inventory if i.item_code == "revival"), None)
    use_revival_from_inventory = inv_item is not None and inv_item.quantity > 0

    if use_revival_from_inventory:
        await self.repository.upsert_inventory(user_id, "revival", -1)
        coin_cost = 0
    else:
        coin_cost = self.REVIVE_COIN_COST
        await self._wallet_service.debit(
            user_id=user_id, amount=coin_cost, asset_code="COIN",
            reason_code="abyss_revive", source_type="run", source_id=run_id,
        )

    # 2. Restore 1 HP
    run = await self.repository.get_run(run_id)
    current_hp = run.mode_state.get("hp", 1)
    new_hp = min((run.mode_state.get("max_hp") or 3), current_hp + 1)

    # 3. Apply 180s shield
    now = datetime.now(tz=UTC)
    shield_expires = now + timedelta(seconds=REVIVE_SHIELD_SECONDS)
    new_mode_state = dict(run.mode_state)
    new_mode_state["hp"] = new_hp
    new_mode_state["revive_shield_expires_at"] = shield_expires.isoformat()
    new_mode_state["revive_shield_count"] = 1

    await self.repository.update_run(run_id, mode_state=new_mode_state)
    await self.repository.commit()

    return {
        "hp_restored": 1,
        "shield_seconds": REVIVE_SHIELD_SECONDS,
        "shield_expires_at": shield_expires.isoformat(),
        "coin_cost": coin_cost,
    }
```

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/services/test_run_service.py -k "revive_prefers_inventory or revive_falls_back" -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/app/services/runs/service.py
git commit -m "feat(shop): revive prefers inventory, shield 180s"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check app/services/runs/service.py && uv run mypy app/services/runs/service.py`

---

### Task 8: 前端 shop.ts API 扩展

**Files:**
- Modify: `frontend/src/api/shop.ts`

**Step 1 — Write failing test (RED)**
```typescript
// frontend/src/api/shop.spec.ts（追加）
describe("useItem", () => {
  it("calls POST /api/v1/shop/use-item", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ success: true, item_code: "xp_boost_2x", quantity_remaining: 2, effect_applied: { type: "xp_boost", multiplier: 2.0 } }),
    });
    const result = await useItem({ itemCode: "xp_boost_2x" });
    expect(result.success).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/shop/use-item",
      expect.objectContaining({ method: "POST" })
    );
  });
});

describe("getActiveEffects", () => {
  it("calls GET /api/v1/shop/active-effects", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true, status: 200,
      text: async () => JSON.stringify({ effects: [{ id: "e1", effect_type: "xp_boost", multiplier: 2.0, expires_at: null }] }),
    });
    const result = await getActiveEffects();
    expect(result.effects[0].multiplier).toBe(2.0);
  });
});
```
Run: `cd frontend && npm run test -- src/api/shop.spec.ts -t "useItem or getActiveEffects"`
Expected: FAIL（函数不存在）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Add to shop.ts**
```typescript
// frontend/src/api/shop.ts（追加）

export type UseItemInput = {
  itemCode: string;
  context?: Record<string, unknown>;
};

export type UseItemResponse = {
  success: boolean;
  item_code: string;
  quantity_remaining: number;
  effect_applied: {
    type: string;
    multiplier?: number;
    expires_at?: string;
    shield_seconds?: number;
  } | null;
};

export type ActiveEffect = {
  id: string;
  effect_type: string;
  multiplier: number | null;
  expires_at: string | null;
  source_item_code: string | null;
  context: Record<string, unknown> | null;
  created_at: string;
};

export type ActiveEffectsResponse = {
  effects: ActiveEffect[];
};

export const useItem = async (input: UseItemInput): Promise<UseItemResponse> => {
  return apiRequest<UseItemResponse>("/api/v1/shop/use-item", {
    method: "POST",
    headers: getAuthHeaders(),
    body: { item_code: input.itemCode, context: input.context ?? null },
  });
};

export const getActiveEffects = async (): Promise<ActiveEffectsResponse> => {
  return apiRequest<ActiveEffectsResponse>("/api/v1/shop/active-effects", {
    headers: getAuthHeaders(),
  });
};
```

**Step 4 — Run test to verify it passes**
Run: `cd frontend && npm run test -- src/api/shop.spec.ts -t "useItem or getActiveEffects"`
Expected: PASS

**Step 5 — Commit**
```bash
git add frontend/src/api/shop.ts
git commit -m "feat(shop): add useItem and getActiveEffects API wrappers"
```

**Step 6 — Linter**
Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 9: 前端 composables — useInventory / useActiveEffects / useStreakProtection

**Files:**
- Create: `frontend/src/composables/useInventory.ts`
- Create: `frontend/src/composables/useActiveEffects.ts`
- Create: `frontend/src/composables/useStreakProtection.ts`

**Step 1 — Write failing test (RED)**
```typescript
// frontend/src/composables/useInventory.spec.ts
describe("useInventory", () => {
  it("fetches and returns inventory items", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true, status: 200,
      text: async () => JSON.stringify({ items: [{ item_code: "xp_boost_2x", quantity: 3 }] }),
    });
    const { inventory, refresh } = useInventory();
    await refresh();
    expect(inventory.value.find(i => i.item_code === "xp_boost_2x")?.quantity).toBe(3);
  });
});

// frontend/src/composables/useActiveEffects.spec.ts
describe("useActiveEffects", () => {
  it("tracks countdown for expiring effects", async () => {
    const future = new Date(Date.now() + 60000).toISOString();
    fetchMock.mockResolvedValueOnce({
      ok: true, status: 200,
      text: async () => JSON.stringify({ effects: [{ id: "e1", effect_type: "xp_boost", multiplier: 2.0, expires_at: future }] }),
    });
    const { effects } = useActiveEffects();
    await effects.refresh();
    expect(effects.value[0].remainingSeconds).toBeGreaterThan(0);
  });
});
```
Run: `cd frontend && npm run test -- src/composables/useInventory.spec.ts src/composables/useActiveEffects.spec.ts -v`
Expected: FAIL

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Write composables**
```typescript
// frontend/src/composables/useInventory.ts
import { ref } from "vue";
import { getShopInventory, type ShopInventoryItem } from "../api/shop";

export function useInventory() {
  const inventory = ref<ShopInventoryItem[]>([]);
  const isLoading = ref(false);

  async function refresh() {
    isLoading.value = true;
    try {
      inventory.value = await getShopInventory();
    } finally {
      isLoading.value = false;
    }
  }

  function quantityOf(itemCode: string): number {
    return inventory.value.find(i => i.item_code === itemCode)?.quantity ?? 0;
  }

  return { inventory, isLoading, refresh, quantityOf };
}

// frontend/src/composables/useActiveEffects.ts
import { ref, computed, onMounted, onUnmounted } from "vue";
import { getActiveEffects, type ActiveEffect } from "../api/shop";

export function useActiveEffects() {
  const effects = ref<(ActiveEffect & { remainingSeconds: number })[]>([]);
  let timer: number | null = null;

  async function refresh() {
    const raw = await getActiveEffects();
    effects.value = raw.effects.map(e => ({
      ...e,
      remainingSeconds: e.expires_at
        ? Math.max(0, Math.floor((new Date(e.expires_at).getTime() - Date.now()) / 1000))
        : Infinity,
    }));
  }

  function startTimer() {
    timer = window.setInterval(() => {
      effects.value = effects.value.map(e => ({
        ...e,
        remainingSeconds: e.expires_at
          ? Math.max(0, Math.floor((new Date(e.expires_at).getTime() - Date.now()) / 1000))
          : Infinity,
      }));
    }, 1000);
  }

  onMounted(() => { refresh(); startTimer(); });
  onUnmounted(() => { if (timer) clearInterval(timer); });

  const activeXpBoost = computed(() =>
    effects.value.find(e => e.effect_type === "xp_boost" && e.remainingSeconds > 0)
  );

  const activeShield = computed(() =>
    effects.value.find(e => e.effect_type === "revive_shield" && e.remainingSeconds > 0)
  );

  return { effects, activeXpBoost, activeShield, refresh };
}

// frontend/src/composables/useStreakProtection.ts
import { computed } from "vue";
import { useInventory } from "./useInventory";

export function useStreakProtection() {
  const { quantityOf } = useInventory();
  const hasStreakFreeze = computed(() => quantityOf("streak_freeze") > 0);
  return { hasStreakFreeze };
}
```

**Step 4 — Run test to verify it passes**
Run: `cd frontend && npm run test -- src/composables/useInventory.spec.ts src/composables/useActiveEffects.spec.ts -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add frontend/src/composables/useInventory.ts frontend/src/composables/useActiveEffects.ts frontend/src/composables/useStreakProtection.ts
git commit -m "feat(shop): add useInventory, useActiveEffects, useStreakProtection composables"
```

**Step 6 — Linter**
Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 10: 前端组件 — ShopItemCard + ShopHeader + ShopActiveEffectsBar

**Files:**
- Create: `frontend/src/components/shop/ShopItemCard.vue`
- Create: `frontend/src/components/shop/ShopHeader.vue`
- Create: `frontend/src/components/shop/ShopActiveEffectsBar.vue`

**Step 1 — Write failing test (RED)**
```typescript
// frontend/src/components/shop/ShopItemCard.spec.ts
import { mount } from "@vue/test-utils";
import ShopItemCard from "./ShopItemCard.vue";

it("renders item name and price", () => {
  const wrapper = mount(ShopItemCard, {
    props: {
      name: "经验翻倍·2x",
      price: 200,
      icon: "⚡",
      accent: "violet",
      itemCode: "xp_boost_2x",
    },
  });
  expect(wrapper.find("h2").text()).toContain("经验翻倍·2x");
  expect(wrapper.find(".price-tag").text()).toContain("200");
});
```
Run: `cd frontend && npm run test -- src/components/shop/ShopItemCard.spec.ts -v`
Expected: FAIL

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Write components**
```vue
<!-- frontend/src/components/shop/ShopItemCard.vue -->
<script setup lang="ts">
defineProps<{
  name: string;
  price: number;
  icon: string;
  accent: "teal" | "violet" | "rose" | "amber";
  itemCode: string;
  priceIsCash?: boolean;
  tag?: string;
  description?: string;
}>();

const emit = defineEmits<{ purchase: [itemCode: string] }>();
</script>

<template>
  <article class="shop-card" :class="`shop-card--${accent}`">
    <div class="shop-card__head">
      <span v-if="tag" class="rarity-tag" :class="`rarity-tag--${accent}`">{{ tag }}</span>
      <span class="price-tag" :class="{ 'price-tag--usd': priceIsCash }">
        {{ priceIsCash ? `$${price}` : `${price} 🪙` }}
      </span>
    </div>
    <div class="shop-card__icon" :class="`shop-card__icon--${accent}`">{{ icon }}</div>
    <div class="shop-card__body">
      <h2>{{ name }}</h2>
      <p>{{ description }}</p>
    </div>
    <footer class="shop-card__footer">
      <button class="purchase-btn" :class="`purchase-btn--${accent}`" type="button"
        @click="emit('purchase', itemCode)">
        {{ priceIsCash ? $t("shop.buyNow") : $t("shop.purchase") }} →
      </button>
    </footer>
  </article>
</template>
```

```vue
<!-- frontend/src/components/shop/ShopHeader.vue -->
<script setup lang="ts">
import ShopWalletPill from "./ShopWalletPill.vue";
import ShopActiveEffectsBar from "./ShopActiveEffectsBar.vue";

defineProps<{ walletBalance: number; onOpenBag: () => void }>();
</script>

<template>
  <header class="shop-header">
    <div class="shop-brand">
      <div class="shop-brand__icon"><img src="/taotie-logo.svg" alt="" /></div>
      <div class="shop-brand__copy"><strong>息壤</strong></div>
    </div>
    <div class="shop-wallet-group">
      <ShopWalletPill :balance="walletBalance" />
      <button class="bag-btn" type="button" aria-label="背包" @click="onOpenBag">👜</button>
    </div>
  </header>
  <ShopActiveEffectsBar />
</template>
```

```vue
<!-- frontend/src/components/shop/ShopActiveEffectsBar.vue -->
<script setup lang="ts">
import { useActiveEffects } from "../../composables/useActiveEffects";
const { effects, activeXpBoost } = useActiveEffects();

function formatTime(secs: number): string {
  if (!Number.isFinite(secs) || secs === Infinity) return "∞";
  const m = Math.floor(secs / 60).toString().padStart(2, "0");
  const s = (secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}
</script>

<template>
  <div v-if="activeXpBoost" class="active-effects-bar">
    <span class="effect-pill effect-pill--violet">
      ⚡ {{ activeXpBoost.multiplier }}x {{ $t("shop.xpBoost") }}
      {{ formatTime(activeXpBoost.remainingSeconds) }}
    </span>
  </div>
</template>
```

**Step 4 — Run test to verify it passes**
Run: `cd frontend && npm run test -- src/components/shop/ShopItemCard.spec.ts -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add frontend/src/components/shop/ShopItemCard.vue frontend/src/components/shop/ShopHeader.vue frontend/src/components/shop/ShopActiveEffectsBar.vue
git commit -m "feat(shop): add ShopItemCard, ShopHeader, ShopActiveEffectsBar components"
```

**Step 6 — Linter**
Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 11: 前端弹窗 — CoinPackTopUpModal + ItemUseConfirmModal + TimeTreasurePromptModal

**Files:**
- Create: `frontend/src/components/shop/modals/CoinPackTopUpModal.vue`
- Create: `frontend/src/components/shop/modals/ItemUseConfirmModal.vue`
- Create: `frontend/src/components/shop/modals/TimeTreasurePromptModal.vue`

**Step 1 — Write failing test (RED)**
```typescript
// frontend/src/components/shop/modals/CoinPackTopUpModal.spec.ts
it("shows tier selection and emits purchase", async () => {
  const wrapper = mount(CoinPackTopUpModal, {
    props: { visible: true },
    global: { plugins: [i18n] },
  });
  expect(wrapper.findAll(".tier-option").length).toBeGreaterThan(1);
  await wrapper.find(".tier-option--recommended").trigger("click");
  await wrapper.find(".confirm-btn").trigger("click");
  expect(wrapper.emitted("purchase")).toBeTruthy();
});
```
Run: `cd frontend && npm run test -- src/components/shop/modals/CoinPackTopUpModal.spec.ts -v`
Expected: FAIL

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Write modals**
```vue
<!-- frontend/src/components/shop/modals/CoinPackTopUpModal.vue -->
<script setup lang="ts">
const props = defineProps<{
  visible: boolean;
  offers: Array<{ id: string; coin_amount: number; price_usd: number; label: string; recommended?: boolean }>;
}>();
const emit = defineEmits<{
  purchase: [offerId: string];
  close: [];
}>();
const selected = ref<string | null>(null);
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="topup-overlay" @click="emit('close')">
      <section class="topup-modal" @click.stop>
        <h2>{{ $t("shop.topUpTitle") }}</h2>
        <div class="tier-list">
          <article v-for="offer in offers" :key="offer.id"
            class="tier-option" :class="{ 'tier-option--selected': selected === offer.id, 'tier-option--recommended': offer.recommended }"
            @click="selected = offer.id">
            <span v-if="offer.recommended" class="recommended-badge">{{ $t("shop.recommended") }}</span>
            <strong>{{ offer.coin_amount }} 🪙</strong>
            <span>${{ offer.price_usd }}</span>
            <small>{{ offer.label }}</small>
          </article>
        </div>
        <footer class="topup-modal__actions">
          <button class="confirm-btn" :disabled="!selected" type="button"
            @click="selected && emit('purchase', selected)">
            {{ $t("shop.confirmPurchase") }}
          </button>
          <button class="cancel-btn" type="button" @click="emit('close')">{{ $t("common.cancel") }}</button>
        </footer>
      </section>
    </div>
  </transition>
</template>
```

```vue
<!-- frontend/src/components/shop/modals/ItemUseConfirmModal.vue -->
<script setup lang="ts">
defineProps<{
  visible: boolean;
  itemName: string;
  itemDescription: string;
  quantity: number;
  actionLabel?: string;
}>();
const emit = defineEmits<{ confirm: []; cancel: []; close: [] }>();
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="item-use-overlay" @click="emit('close')">
      <section class="item-use-modal" @click.stop>
        <h2>{{ itemName }}</h2>
        <p>{{ itemDescription }}</p>
        <p class="item-use-modal__qty">{{ $t("shop.inInventory", { n: quantity }) }}</p>
        <footer class="item-use-modal__actions">
          <button class="confirm-btn" type="button" @click="emit('confirm')">
            {{ actionLabel || $t("shop.useNow") }}
          </button>
          <button class="cancel-btn" type="button" @click="emit('cancel')">{{ $t("common.cancel") }}</button>
        </footer>
      </section>
    </div>
  </transition>
</template>
```

```vue
<!-- frontend/src/components/shop/modals/TimeTreasurePromptModal.vue -->
<script setup lang="ts">
defineProps<{
  visible: boolean;
  currentBoostMultiplier: number;
  remainingSeconds: number;
  timeTreasureQuantity: number;
}>();
const emit = defineEmits<{ useTimeTreasure: []; buyMore: []; dismiss: []; close: [] }>();

function fmt(secs: number) {
  return `${Math.floor(secs / 60)}:${(secs % 60).toString().padStart(2, "0")}`;
}
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="time-prompt-overlay" @click="emit('close')">
      <section class="time-prompt-modal" @click.stop>
        <h2>{{ $t("shop.boostExpiringTitle") }}</h2>
        <p>{{ $t("shop.boostExpiringDesc", { multiplier: currentBoostMultiplier, time: fmt(remainingSeconds) }) }}</p>
        <p>{{ $t("shop.timeTreasureAvailable", { n: timeTreasureQuantity }) }}</p>
        <footer class="time-prompt-modal__actions">
          <button class="confirm-btn" type="button" @click="emit('useTimeTreasure')">
            {{ $t("shop.useTimeTreasure") }} ({{ timeTreasureQuantity }})
          </button>
          <button class="secondary-btn" type="button" @click="emit('buyMore')">{{ $t("shop.buyMore") }}</button>
          <button class="cancel-btn" type="button" @click="emit('dismiss')">{{ $t("shop.letItExpire") }}</button>
        </footer>
      </section>
    </div>
  </transition>
</template>
```

**Step 4 — Run test to verify it passes**
Run: `cd frontend && npm run test -- src/components/shop/modals/CoinPackTopUpModal.spec.ts -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add frontend/src/components/shop/modals/CoinPackTopUpModal.vue frontend/src/components/shop/modals/ItemUseConfirmModal.vue frontend/src/components/shop/modals/TimeTreasurePromptModal.vue
git commit -m "feat(shop): add CoinPackTopUpModal, ItemUseConfirmModal, TimeTreasurePromptModal"
```

**Step 6 — Linter**
Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 12: 前端弹窗 — AbyssReviveModal（从 EndlessAbyssPage 提取）

**Files:**
- Create: `frontend/src/components/shop/modals/AbyssReviveModal.vue`
- Modify: `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`（用组件替换内联弹窗）

**Step 1 — Write failing test (RED)**
```typescript
// frontend/src/components/shop/modals/AbyssReviveModal.spec.ts
it("shows use from inventory when quantity > 0", async () => {
  const wrapper = mount(AbyssReviveModal, {
    props: { visible: true, revivalQuantity: 2, reviveCost: 10, canAfford: true },
    global: { plugins: [i18n] },
  });
  expect(wrapper.find(".revive-modal__actions .cast-btn").text()).toContain("2");
});
```
Run: `cd frontend && npm run test -- src/components/shop/modals/AbyssReviveModal.spec.ts -v`
Expected: FAIL

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Extract to component**
```vue
<!-- frontend/src/components/shop/modals/AbyssReviveModal.vue -->
<script setup lang="ts">
const props = defineProps<{
  visible: boolean;
  revivalQuantity: number;  // 背包中复活币数量
  reviveCost: number;        // 即时购买价格（COIN）
  canAfford: boolean;        // 当前 COIN 是否够即时购买
  shieldExpiresAt: string | null;
  error?: string;
}>();
const emit = defineEmits<{
  useFromInventory: [];
  buyAndUse: [];
  leave: [];
  close: [];
}>();
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="revive-overlay" @click="emit('close')">
      <div class="revive-modal" role="dialog" @click.stop>
        <p class="revive-modal__eyebrow">{{ $t("endlessAbyss.reviveModal.eyebrow") }}</p>
        <h2>{{ $t("endlessAbyss.reviveModal.title") }}</h2>
        <p>{{ $t("endlessAbyss.reviveModal.description") }}</p>
        <p v-if="shieldExpiresAt" class="revive-modal__buff">
          {{ $t("endlessAbyss.reviveModal.shieldActive", { time: shieldExpiresAt }) }}
        </p>
        <p v-if="error" class="revive-modal__error">{{ error }}</p>
        <div class="revive-modal__actions">
          <!-- 优先：背包有库存 -->
          <button v-if="revivalQuantity > 0" class="cast-btn" type="button"
            @click="emit('useFromInventory')">
            {{ $t("shop.useRevivalFromBag", { n: revivalQuantity }) }}
          </button>
          <!-- 其次：余额够，购买并使用 -->
          <button v-else-if="canAfford" class="cast-btn" type="button"
            @click="emit('buyAndUse')">
            {{ $t("shop.buyAndUseRevival", { cost: reviveCost }) }}
          </button>
          <!-- 否则：余额不够，购买充值 -->
          <button v-else class="cast-btn" type="button"
            @click="emit('buyAndUse')">
            {{ $t("shop.buyRevivalAndRecharge", { cost: reviveCost }) }}
          </button>
          <button class="return-btn" type="button" @click="emit('leave')">
            {{ $t("endlessAbyss.reviveModal.leave") }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>
```

**Step 4 — Run test to verify it passes**
Run: `cd frontend && npm run test -- src/components/shop/modals/AbyssReviveModal.spec.ts -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add frontend/src/components/shop/modals/AbyssReviveModal.vue
git commit -m "feat(shop): extract AbyssReviveModal from EndlessAbyssPage"
```

**Step 6 — Linter**
Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 13: 前端 ShopPage 重构 — 整合所有组件

**Files:**
- Modify: `frontend/src/pages/DungeonScholarShopPage.vue`（重写为组件化架构）

**Step 1 — Write failing test (RED)**
```typescript
// frontend/src/pages/DungeonScholarShopPage.spec.ts（追加）
it("renders recharge and item sections", async () => {
  mocks.listShopItems.mockResolvedValue([
    { id: "c1", item_code: "coin_pack_medium", price_amount: 199, display_name: "金币包·中", rarity: "uncommon" },
    { id: "xp1", item_code: "xp_boost_2x", price_amount: 260, display_name: "经验翻倍·2x", rarity: "rare" },
  ]);
  // ... mount and assert grid sections exist
  expect(wrapper.find(".recharge-section")).toBeTruthy();
  expect(wrapper.find(".items-section")).toBeTruthy();
});
```
Run: `cd frontend && npm run test -- src/pages/DungeonScholarShopPage.spec.ts -v`
Expected: FAIL（结构不匹配）

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Rewrite ShopPage**
```vue
<!-- frontend/src/pages/DungeonScholarShopPage.vue -->
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import ShopHeader from "../components/shop/ShopHeader.vue";
import ShopHero from "../components/shop/ShopHero.vue";
import ShopItemCard from "../components/shop/ShopItemCard.vue";
import CoinPackTopUpModal from "../components/shop/modals/CoinPackTopUpModal.vue";
import ItemUseConfirmModal from "../components/shop/modals/ItemUseConfirmModal.vue";
import { useShopItems } from "../composables/useShopItems";
import { useInventory } from "../composables/useInventory";
import { useActiveEffects } from "../composables/useActiveEffects";

const { walletBalance, shopItems, isLoading, fetchBalance, fetchItems, purchaseItem } = useShopItems();
const { inventory, refreshInventory } = useInventory();
const { activeXpBoost } = useActiveEffects();

const showTopUpModal = ref(false);
const showUseModal = ref(false);
const selectedItem = ref<ShopOffer | null>(null);

onMounted(async () => {
  await Promise.all([fetchBalance(), fetchItems()]);
});

const coinPacks = computed(() => shopItems.value.filter(i => i.item_code.startsWith("coin_pack")));
const tools = computed(() => shopItems.value.filter(i => ["streak_freeze","xp_boost_1_5x","xp_boost_2x","xp_boost_3x","time_treasure","revival"].includes(i.item_code)));

function handlePurchase(item: ShopOffer) {
  selectedItem.value = item;
  if (item.item_code.startsWith("coin_pack")) {
    showTopUpModal.value = true;
  } else {
    showUseModal.value = true;
  }
}

async function onTopUpPurchase(offerId: string) {
  await purchaseItem({ offerId });
  showTopUpModal.value = false;
  await Promise.all([fetchBalance(), fetchItems()]);
}

async function onItemUseConfirm() {
  if (!selectedItem.value) return;
  await purchaseItem({ offerId: selectedItem.value.id });
  showUseModal.value = false;
  await Promise.all([fetchBalance(), fetchItems(), refreshInventory()]);
}
</script>

<template>
  <main class="shop-page">
    <section class="shop-shell">
      <ShopHeader :wallet-balance="walletBalance" @open-bag="refreshInventory" />
      <ShopHero />
      <div class="shop-divider" />

      <!-- 代币充值区 -->
      <section class="recharge-section">
        <h2 class="section-title">{{ $t("shop.rechargeTitle") }}</h2>
        <div class="shop-grid">
          <ShopItemCard v-for="item in coinPacks" :key="item.id"
            :name="item.display_name" :price="item.price_amount" icon="💎" accent="amber"
            :item-code="item.item_code" price-is-cash :tag="$t('shop.topUp')"
            @purchase="handlePurchase(item)" />
        </div>
      </section>

      <!-- 道具区 -->
      <section class="items-section">
        <h2 class="section-title">{{ $t("shop.itemsTitle") }}</h2>
        <div class="shop-grid">
          <ShopItemCard v-for="item in tools" :key="item.id"
            :name="item.display_name" :price="item.price_amount" icon="..." accent="violet"
            :item-code="item.item_code" :tag="item.rarity"
            @purchase="handlePurchase(item)" />
        </div>
      </section>
    </section>

    <CoinPackTopUpModal :visible="showTopUpModal" :offers="coinPacks" @purchase="onTopUpPurchase" @close="showTopUpModal = false" />
    <ItemUseConfirmModal :visible="showUseModal" :item-name="selectedItem?.display_name ?? ''"
      :description="selectedItem?.display_name ?? ''" :quantity="inventory.find(i => i.item_code === selectedItem?.item_code)?.quantity ?? 0"
      @confirm="onItemUseConfirm" @cancel="showUseModal = false" @close="showUseModal = false" />
  </main>
</template>
```

**Step 4 — Run test to verify it passes**
Run: `cd frontend && npm run test -- src/pages/DungeonScholarShopPage.spec.ts -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add frontend/src/pages/DungeonScholarShopPage.vue
git commit -m "feat(shop): refactor ShopPage into component architecture"
```

**Step 6 — Linter**
Run: `cd frontend && npm run lint && npm run typecheck && npm run build`

---

### Task 14: 集成测试 — 购买 → 入库 → 使用 → 结算翻倍 端到端

**Files:**
- Create: `backend/tests/integration/test_shop_items_full_flow.py`
- Create: `frontend/src/e2e/shop-flow.spec.ts`

**Step 1 — Write failing test (RED)**
```python
# backend/tests/integration/test_shop_items_full_flow.py
async def test_full_flow_xp_boost_purchase_to_settlement(db_session, client, fake_auth, user_id):
    # 1. 购买 xp_boost_2x offer
    offer = await create_offer(db_session, item_code="xp_boost_2x", price=200)
    purchase_resp = client.post("/api/v1/shop/purchase", json={"offer_id": str(offer.id)}, headers=fake_auth)
    assert purchase_resp.status_code == 200

    # 2. 使用道具
    use_resp = client.post("/api/v1/shop/use-item", json={"item_code": "xp_boost_2x"}, headers=fake_auth)
    assert use_resp.status_code == 200
    assert use_resp.json()["effect_applied"]["multiplier"] == 2.0

    # 3. 完成 run，验证结算 XP 翻倍
    run_resp = client.post("/api/v1/runs", json={"document_id": str(doc_id), "mode": "endless", "question_count": 5}, headers=fake_auth)
    # ... submit answers, get settlement
    assert settlement["xp_earned"] == 200  # base 100 * 2.0
```
Run: `uv run pytest tests/integration/test_shop_items_full_flow.py -v`
Expected: FAIL

**Step 2 — Run test to verify it fails**
Expected: FAIL

**Step 3 — Implement and fix any integration gaps**
（根据测试失败信息，修复接口不兼容、数据不对等问题）

**Step 4 — Run test to verify it passes**
Run: `uv run pytest tests/integration/test_shop_items_full_flow.py -v`
Expected: PASS

**Step 5 — Commit**
```bash
git add backend/tests/integration/test_shop_items_full_flow.py frontend/src/e2e/shop-flow.spec.ts
git commit -m "test(shop): add full flow integration tests"
```

**Step 6 — Linter**
Run: `cd backend && uv run ruff check tests/integration/test_shop_items_full_flow.py && cd frontend && npm run lint`
