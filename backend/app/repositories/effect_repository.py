from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import delete, select, update

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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
        context: dict[str, Any] | None = None,
    ) -> UUID:
        from app.db.models.economy import ActiveEffect

        model = ActiveEffect(
            user_id=user_id,
            effect_type=effect_type,
            multiplier=multiplier,
            expires_at=expires_at,
            source_item_code=source_item_code,
            source_use_id=source_use_id,
            context=context or {},
        )
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def list_active_effects(self, user_id: UUID) -> list[Any]:
        from app.db.models.economy import ActiveEffect

        now = datetime.now(UTC)
        stmt = (
            select(ActiveEffect)
            .where(ActiveEffect.user_id == user_id)
            .where((ActiveEffect.expires_at.is_(None)) | (ActiveEffect.expires_at > now))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_expired_effects(self, user_id: UUID) -> None:
        from app.db.models.economy import ActiveEffect

        now = datetime.now(UTC)
        stmt = delete(ActiveEffect).where(
            ActiveEffect.user_id == user_id,
            ActiveEffect.expires_at.is_not(None),
            ActiveEffect.expires_at <= now,
        )
        await self._session.execute(stmt)

    async def update_expires(self, effect_id: UUID, expires_at: datetime) -> None:
        from app.db.models.economy import ActiveEffect

        stmt = (
            update(ActiveEffect).where(ActiveEffect.id == effect_id).values(expires_at=expires_at)
        )
        await self._session.execute(stmt)

    async def record_use(
        self,
        *,
        user_id: UUID,
        item_code: str,
        inventory_id: UUID | None = None,
        effect_snapshot: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> UUID:
        from app.db.models.economy import UseRecord

        model = UseRecord(
            user_id=user_id,
            item_code=item_code,
            inventory_id=inventory_id,
            effect_snapshot=effect_snapshot or {},
            context=context or {},
        )
        self._session.add(model)
        await self._session.flush()
        return model.id
