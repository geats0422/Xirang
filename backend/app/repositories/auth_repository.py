from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import delete as sql_delete
from sqlalchemy import select

from app.db.models.auth import AuthCredential, AuthSession, User, UserStatus
from app.db.models.economy import Wallet
from app.db.models.profile import Profile, UserSetting

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email_normalized: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email_normalized == email_normalized, User.deleted_at.is_(None))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username_normalized: str) -> User | None:
        stmt = (
            select(User)
            .where(User.username_normalized == username_normalized, User.deleted_at.is_(None))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None)).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        username: str,
        username_normalized: str,
        email: str,
        email_normalized: str,
    ) -> User:
        user = User(
            username=username,
            username_normalized=username_normalized,
            email=email,
            email_normalized=email_normalized,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_auth_credential(self, *, user_id: UUID, password_hash: str) -> AuthCredential:
        credential = AuthCredential(user_id=user_id, password_hash=password_hash)
        self._session.add(credential)
        await self._session.flush()
        return credential

    async def create_profile_for_user(self, *, user_id: UUID) -> Profile:
        profile = Profile(user_id=user_id)
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def create_settings_for_user(self, *, user_id: UUID) -> UserSetting:
        settings = UserSetting(user_id=user_id)
        self._session.add(settings)
        await self._session.flush()
        return settings

    async def create_wallet_for_user(self, *, user_id: UUID) -> Wallet:
        wallet = Wallet(user_id=user_id)
        self._session.add(wallet)
        await self._session.flush()
        return wallet

    async def get_auth_credential(self, user_id: UUID) -> AuthCredential | None:
        stmt = select(AuthCredential).where(AuthCredential.user_id == user_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_auth_session(
        self,
        *,
        user_id: UUID,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> AuthSession:
        session = AuthSession(
            user_id=user_id,
            session_token_hash=session_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def get_auth_session(self, session_id: UUID) -> AuthSession | None:
        stmt = select(AuthSession).where(AuthSession.id == session_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_auth_session_tokens(
        self,
        *,
        session_id: UUID,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> AuthSession | None:
        session = await self.get_auth_session(session_id)
        if session is None:
            return None

        session.session_token_hash = session_token_hash
        session.refresh_token_hash = refresh_token_hash
        session.expires_at = expires_at
        await self._session.flush()
        return session

    async def revoke_auth_session(
        self, *, session_id: UUID, revoked_at: datetime
    ) -> AuthSession | None:
        session = await self.get_auth_session(session_id)
        if session is None:
            return None

        session.revoked_at = revoked_at
        await self._session.flush()
        return session

    async def update_last_login(self, *, user_id: UUID, last_login_at: datetime) -> User | None:
        user = await self.get_user_by_id(user_id)
        if user is None:
            return None

        user.last_login_at = last_login_at
        await self._session.flush()
        return user

    async def soft_delete_user(self, *, user_id: UUID) -> User | None:
        user = await self.get_user_by_id(user_id)
        if user is None:
            return None
        user.deleted_at = datetime.now(UTC)
        user.status = UserStatus.DELETED
        await self._session.flush()
        return user

    async def hard_delete_user_game_data(self, *, user_id: UUID) -> None:
        from sqlalchemy import ColumnElement

        from app.db.models.documents import Document
        from app.db.models.economy import (
            ActiveEffect,
            Inventory,
            LeaderboardSnapshot,
            PurchaseRecord,
            UseRecord,
            WalletLedger,
        )
        from app.db.models.review import Mistake, MistakeEmbedding, QuestionFeedback
        from app.db.models.runs import Run, RunAnswer, RunQuestion, Settlement

        run_ids_stmt = select(Run.id).where(Run.user_id == user_id)
        mistake_ids_stmt = select(Mistake.id).where(Mistake.user_id == user_id)
        tables_to_delete: list[tuple[type, ColumnElement[bool]]] = [
            (RunAnswer, RunAnswer.run_id.in_(run_ids_stmt)),
            (RunQuestion, RunQuestion.run_id.in_(run_ids_stmt)),
            (Settlement, Settlement.user_id == user_id),
            (Run, Run.user_id == user_id),
            (MistakeEmbedding, MistakeEmbedding.mistake_id.in_(mistake_ids_stmt)),
            (Mistake, Mistake.user_id == user_id),
            (QuestionFeedback, QuestionFeedback.user_id == user_id),
            (ActiveEffect, ActiveEffect.user_id == user_id),
            (UseRecord, UseRecord.user_id == user_id),
            (Inventory, Inventory.user_id == user_id),
            (PurchaseRecord, PurchaseRecord.user_id == user_id),
            (WalletLedger, WalletLedger.user_id == user_id),
            (LeaderboardSnapshot, LeaderboardSnapshot.user_id == user_id),
            (Document, Document.owner_user_id == user_id),
        ]
        for model, condition in tables_to_delete:
            await self._session.execute(sql_delete(model).where(condition))
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
