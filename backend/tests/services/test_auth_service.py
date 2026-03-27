from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.services.auth.passwords import PasswordService
from app.services.auth.service import (
    AuthService,
    DuplicateIdentityError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.services.auth.tokens import TokenService


@dataclass
class FakeUser:
    id: UUID
    username: str
    username_normalized: str
    email: str
    email_normalized: str
    status: str = "active"
    last_login_at: datetime | None = None


@dataclass
class FakeCredential:
    user_id: UUID
    password_hash: str


@dataclass
class FakeSession:
    id: UUID
    user_id: UUID
    session_token_hash: str
    refresh_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, FakeUser] = {}
        self.credentials: dict[UUID, FakeCredential] = {}
        self.sessions: dict[UUID, FakeSession] = {}
        self.commit_count = 0
        self.rollback_count = 0

    async def get_user_by_email(self, email_normalized: str) -> FakeUser | None:
        return next(
            (user for user in self.users.values() if user.email_normalized == email_normalized),
            None,
        )

    async def get_user_by_username(self, username_normalized: str) -> FakeUser | None:
        return next(
            (
                user
                for user in self.users.values()
                if user.username_normalized == username_normalized
            ),
            None,
        )

    async def get_user_by_id(self, user_id: UUID) -> FakeUser | None:
        return self.users.get(user_id)

    async def create_user(
        self, *, username: str, username_normalized: str, email: str, email_normalized: str
    ) -> FakeUser:
        user = FakeUser(
            id=uuid4(),
            username=username,
            username_normalized=username_normalized,
            email=email,
            email_normalized=email_normalized,
        )
        self.users[user.id] = user
        return user

    async def create_auth_credential(self, *, user_id: UUID, password_hash: str) -> FakeCredential:
        credential = FakeCredential(user_id=user_id, password_hash=password_hash)
        self.credentials[user_id] = credential
        return credential

    async def create_profile_for_user(self, *, user_id: UUID) -> None:
        return None

    async def create_settings_for_user(self, *, user_id: UUID) -> None:
        return None

    async def create_wallet_for_user(self, *, user_id: UUID) -> None:
        return None

    async def get_auth_credential(self, user_id: UUID) -> FakeCredential | None:
        return self.credentials.get(user_id)

    async def create_auth_session(
        self,
        *,
        user_id: UUID,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> FakeSession:
        session = FakeSession(
            id=uuid4(),
            user_id=user_id,
            session_token_hash=session_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self.sessions[session.id] = session
        return session

    async def get_auth_session(self, session_id: UUID) -> FakeSession | None:
        return self.sessions.get(session_id)

    async def update_auth_session_tokens(
        self,
        *,
        session_id: UUID,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> FakeSession:
        session = self.sessions[session_id]
        session.session_token_hash = session_token_hash
        session.refresh_token_hash = refresh_token_hash
        session.expires_at = expires_at
        return session

    async def revoke_auth_session(self, *, session_id: UUID, revoked_at: datetime) -> None:
        self.sessions[session_id].revoked_at = revoked_at

    async def update_last_login(self, *, user_id: UUID, last_login_at: datetime) -> None:
        self.users[user_id].last_login_at = last_login_at

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


def build_auth_service() -> tuple[AuthService, FakeAuthRepository]:
    repository = FakeAuthRepository()
    service = AuthService(
        repository=repository,
        password_service=PasswordService(),
        token_service=TokenService(
            secret_key="test-secret",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        ),
    )
    return service, repository


@pytest.mark.asyncio
async def test_register_creates_user_and_session_tokens() -> None:
    service, repository = build_auth_service()

    result = await service.register(
        username="Hero", email="hero@example.com", password="Secret-pass1"
    )

    assert result.user.username == "Hero"
    assert result.user.email == "hero@example.com"
    assert result.tokens.access_token
    assert result.tokens.refresh_token
    assert repository.commit_count == 1
    assert len(repository.sessions) == 1


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email() -> None:
    service, _ = build_auth_service()

    await service.register(username="Hero", email="hero@example.com", password="Secret-pass1")

    with pytest.raises(DuplicateIdentityError):
        await service.register(username="Mage", email="hero@example.com", password="Another-pass1")


@pytest.mark.asyncio
async def test_login_accepts_email_identity_and_updates_last_login() -> None:
    service, repository = build_auth_service()
    registered = await service.register(
        username="Hero", email="hero@example.com", password="Secret-pass1"
    )

    result = await service.login(identity="hero@example.com", password="Secret-pass1")

    assert result.user.id == registered.user.id
    assert repository.users[result.user.id].last_login_at is not None


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    service, _ = build_auth_service()
    await service.register(username="Hero", email="hero@example.com", password="Secret-pass1")

    with pytest.raises(InvalidCredentialsError):
        await service.login(identity="hero@example.com", password="Bad-pass1")


@pytest.mark.asyncio
async def test_refresh_rotates_session_and_invalidates_previous_refresh_token() -> None:
    service, repository = build_auth_service()
    registered = await service.register(
        username="Hero", email="hero@example.com", password="Secret-pass1"
    )
    initial_session = next(iter(repository.sessions.values()))
    initial_refresh = registered.tokens.refresh_token
    initial_session_hash = initial_session.session_token_hash

    refreshed = await service.refresh(refresh_token=initial_refresh)

    assert refreshed.tokens.refresh_token != initial_refresh
    assert repository.sessions[initial_session.id].session_token_hash != initial_session_hash

    with pytest.raises(InvalidTokenError):
        await service.refresh(refresh_token=initial_refresh)


@pytest.mark.asyncio
async def test_logout_revokes_current_session_and_me_rejects_old_access_token() -> None:
    service, repository = build_auth_service()
    registered = await service.register(
        username="Hero", email="hero@example.com", password="Secret-pass1"
    )
    session = next(iter(repository.sessions.values()))

    await service.logout(access_token=registered.tokens.access_token)

    assert repository.sessions[session.id].revoked_at is not None

    with pytest.raises(InvalidTokenError):
        await service.get_current_user(access_token=registered.tokens.access_token)


@pytest.mark.asyncio
async def test_get_current_user_returns_user_for_valid_access_token() -> None:
    service, _ = build_auth_service()
    registered = await service.register(
        username="Hero", email="hero@example.com", password="Secret-pass1"
    )

    user = await service.get_current_user(access_token=registered.tokens.access_token)

    assert user.id == registered.user.id


def test_token_service_marks_refresh_token_expiry_later_than_access_token() -> None:
    token_service = TokenService(
        secret_key="test-secret",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )

    access = token_service.build_access_token(
        user_id=uuid4(), session_id=uuid4(), session_token="session-token"
    )
    refresh = token_service.build_refresh_token(
        user_id=uuid4(), session_id=uuid4(), session_token="session-token"
    )

    access_payload = token_service.decode_token(access.token, expected_token_type="access")
    refresh_payload = token_service.decode_token(refresh.token, expected_token_type="refresh")

    access_exp = datetime.fromtimestamp(access_payload.exp, tz=UTC)
    refresh_exp = datetime.fromtimestamp(refresh_payload.exp, tz=UTC)
    assert refresh_exp - access_exp > timedelta(days=6)
