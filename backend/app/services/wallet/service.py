from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from app.schemas.shop import BalanceResponse

if TYPE_CHECKING:
    from uuid import UUID


class WalletLedgerProtocol(Protocol):
    user_id: UUID
    asset_code: str
    delta: int
    balance_after: int


class WalletRepositoryProtocol(Protocol):
    async def get_balance(self, user_id: UUID, asset_code: str) -> int: ...
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
    ) -> WalletLedgerProtocol: ...
    async def get_ledger_by_idempotency_key(
        self, idempotency_key: str
    ) -> WalletLedgerProtocol | None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class WalletServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InsufficientBalanceError(WalletServiceError):
    status_code = 400


class WalletService:
    """Service for managing user wallet balances and transactions."""

    def __init__(self, *, repository: Any) -> None:
        self.repository: WalletRepositoryProtocol = cast("WalletRepositoryProtocol", repository)

    async def get_balance(self, user_id: UUID, asset_code: str = "COIN") -> BalanceResponse:
        """Get user's wallet balance for an asset.

        Args:
            user_id: The user's ID.
            asset_code: The asset code (e.g., "COIN", "XP").

        Returns:
            The user's balance for the specified asset.
        """
        balance = await self.repository.get_balance(user_id, asset_code)
        return BalanceResponse(asset_code=asset_code, balance=balance)

    async def debit(
        self,
        *,
        user_id: UUID,
        amount: int,
        asset_code: str = "COIN",
        reason_code: str,
        source_type: str | None = None,
        source_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> WalletLedgerProtocol:
        """Debit (subtract) from user's wallet balance.

        Args:
            user_id: The user's ID.
            amount: Amount to debit.
            asset_code: The asset code (default: "COIN").
            reason_code: Reason for the debit.
            source_type: Type of source (optional).
            source_id: ID of source (optional).
            idempotency_key: Key to prevent duplicate transactions.

        Returns:
            The ledger entry for the transaction.

        Raises:
            InsufficientBalanceError: If balance is insufficient.
        """
        if idempotency_key:
            existing = await self.repository.get_ledger_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        current_balance = await self.repository.get_balance(user_id, asset_code)
        if current_balance < amount:
            raise InsufficientBalanceError("Insufficient balance")

        return await self.repository.create_ledger_entry(
            user_id=user_id,
            asset_code=asset_code,
            delta=-amount,
            reason_code=reason_code,
            source_type=source_type,
            source_id=source_id,
            idempotency_key=idempotency_key,
        )

    async def credit(
        self,
        *,
        user_id: UUID,
        amount: int,
        asset_code: str = "COIN",
        reason_code: str,
        source_type: str | None = None,
        source_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> WalletLedgerProtocol:
        if amount < 0:
            raise WalletServiceError("Credit amount must be non-negative")

        if idempotency_key:
            existing = await self.repository.get_ledger_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        return await self.repository.create_ledger_entry(
            user_id=user_id,
            asset_code=asset_code,
            delta=amount,
            reason_code=reason_code,
            source_type=source_type,
            source_id=source_id,
            idempotency_key=idempotency_key,
        )
