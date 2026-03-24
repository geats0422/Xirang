from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from app.db.models.economy import Wallet, WalletLedger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_balance(self, user_id: UUID, asset_code: str) -> int:
        stmt = select(func.coalesce(func.sum(WalletLedger.delta), 0)).where(
            WalletLedger.user_id == user_id, WalletLedger.asset_code == asset_code
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def create_ledger_entry(
        self,
        *,
        user_id: UUID,
        asset_code: str,
        delta: int,
        reason_code: str,
        source_type: str | None = None,
        source_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> WalletLedger:
        wallet_stmt = select(Wallet).where(Wallet.user_id == user_id).limit(1)
        wallet_result = await self._session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()
        if wallet is None:
            wallet = Wallet(user_id=user_id)
            self._session.add(wallet)
            await self._session.flush()

        current_balance = await self.get_balance(user_id, asset_code)
        entry = WalletLedger(
            user_id=user_id,
            asset_code=asset_code,
            delta=delta,
            balance_after=current_balance + delta,
            reason_code=reason_code,
            source_type=source_type,
            source_id=source_id,
            idempotency_key=idempotency_key,
            created_at=datetime.now(UTC),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_ledger_by_idempotency_key(self, idempotency_key: str) -> WalletLedger | None:
        stmt = select(WalletLedger).where(WalletLedger.idempotency_key == idempotency_key).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_ledger(
        self,
        *,
        user_id: UUID,
        asset_code: str = "COIN",
        limit: int = 50,
        offset: int = 0,
    ) -> list[WalletLedger]:
        stmt = (
            select(WalletLedger)
            .where(WalletLedger.user_id == user_id, WalletLedger.asset_code == asset_code)
            .order_by(WalletLedger.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
