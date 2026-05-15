from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.services.auth.passwords import PasswordService
from app.services.auth.service import (
    AuthService,
    AuthServiceError,
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
    email_verified_at: datetime | None = None


@dataclass
class FakeVerificationCode:
    id: UUID
    email_normalized: str
    code_hash: str
    purpose: str
    attempt_count: int
    max_attempts: int
    expires_at: datetime
    consumed_at: datetime | None
    last_sent_at: datetime
    created_at: datetime


class FakeMailClient:
    def __init__(self) -> None:
        self.sent_codes: list[tuple[str, str]] = []

    async def send_verification_code(self, *, email: str, code: str, idempotency_key: str) -> None:
        _ = idempotency_key
        self.sent_codes.append((email, code))


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
        self.verification_codes: list[FakeVerificationCode] = []
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
        self,
        *,
        username: str,
        username_normalized: str,
        email: str,
        email_normalized: str,
        email_verified_at: datetime | None = None,
    ) -> FakeUser:
        user = FakeUser(
            id=uuid4(),
            username=username,
            username_normalized=username_normalized,
            email=email,
            email_normalized=email_normalized,
            email_verified_at=email_verified_at,
        )
        self.users[user.id] = user
        return user

    async def create_email_verification_code(
        self,
        *,
        email_normalized: str,
        code_hash: str,
        purpose: str,
        max_attempts: int,
        expires_at: datetime,
        last_sent_at: datetime,
    ) -> FakeVerificationCode:
        record = FakeVerificationCode(
            id=uuid4(),
            email_normalized=email_normalized,
            code_hash=code_hash,
            purpose=purpose,
            attempt_count=0,
            max_attempts=max_attempts,
            expires_at=expires_at,
            consumed_at=None,
            last_sent_at=last_sent_at,
            created_at=last_sent_at,
        )
        self.verification_codes.append(record)
        return record

    async def get_latest_email_verification_code(
        self, *, email_normalized: str, purpose: str
    ) -> FakeVerificationCode | None:
        matches = [
            item
            for item in self.verification_codes
            if item.email_normalized == email_normalized and item.purpose == purpose
        ]
        return matches[-1] if matches else None

    async def increment_email_verification_attempts(self, *, code_id: UUID) -> None:
        record = next(item for item in self.verification_codes if item.id == code_id)
        record.attempt_count += 1

    async def consume_email_verification_code(
        self, *, code_id: UUID, consumed_at: datetime
    ) -> None:
        record = next(item for item in self.verification_codes if item.id == code_id)
        record.consumed_at = consumed_at

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


def build_auth_service() -> tuple[AuthService, FakeAuthRepository, FakeMailClient]:
    repository = FakeAuthRepository()
    mail_client = FakeMailClient()
    service = AuthService(
        repository=repository,
        password_service=PasswordService(),
        token_service=TokenService(
            secret_key="test-secret",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        ),
        verification_secret="verification-secret",
        mail_client=mail_client,
        verification_ttl_seconds=600,
        verification_resend_cooldown_seconds=60,
        verification_max_attempts=5,
    )
    return service, repository, mail_client


async def send_code_and_get_plain(service: AuthService, mail_client: FakeMailClient) -> str:
    await service.send_registration_verification_code(email="hero@example.com")
    return mail_client.sent_codes[-1][1]


@pytest.mark.asyncio
async def test_register_creates_user_and_session_tokens() -> None:
    service, repository, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)

    result = await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
    )

    assert result.user.username == "Hero"
    assert result.user.email == "hero@example.com"
    assert result.tokens.access_token
    assert result.tokens.refresh_token
    assert repository.commit_count == 2
    assert len(repository.sessions) == 1
    assert result.user.email_verified_at is not None
    assert repository.verification_codes[-1].consumed_at is not None


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email() -> None:
    service, _, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)

    await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
    )

    with pytest.raises(DuplicateIdentityError):
        await service.register(
            username="Mage",
            email="hero@example.com",
            password="Another-pass1",
            verification_code=code,
        )


@pytest.mark.asyncio
async def test_send_registration_verification_code_rejects_resend_cooldown() -> None:
    service, _, _ = build_auth_service()

    await service.send_registration_verification_code(email="hero@example.com")

    with pytest.raises(AuthServiceError, match="Please wait before requesting another code"):
        await service.send_registration_verification_code(email="hero@example.com")


@pytest.mark.asyncio
async def test_register_rejects_invalid_verification_code_and_counts_attempt() -> None:
    service, repository, mail_client = build_auth_service()
    await send_code_and_get_plain(service, mail_client)

    with pytest.raises(AuthServiceError, match="Invalid verification code"):
        await service.register(
            username="Hero",
            email="hero@example.com",
            password="Secret-pass1",
            verification_code="000000",
        )

    assert repository.verification_codes[-1].attempt_count == 1


@pytest.mark.asyncio
async def test_register_rejects_expired_verification_code() -> None:
    service, repository, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)
    repository.verification_codes[-1].expires_at = datetime.now(UTC) - timedelta(seconds=1)

    with pytest.raises(AuthServiceError, match="Verification code expired"):
        await service.register(
            username="Hero",
            email="hero@example.com",
            password="Secret-pass1",
            verification_code=code,
        )


@pytest.mark.asyncio
async def test_login_accepts_email_identity_and_updates_last_login() -> None:
    service, repository, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)
    registered = await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
    )

    result = await service.login(identity="hero@example.com", password="Secret-pass1")

    assert result.user.id == registered.user.id
    assert repository.users[result.user.id].last_login_at is not None


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    service, _, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)
    await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
    )

    with pytest.raises(InvalidCredentialsError):
        await service.login(identity="hero@example.com", password="Bad-pass1")


@pytest.mark.asyncio
async def test_refresh_rotates_session_and_invalidates_previous_refresh_token() -> None:
    service, repository, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)
    registered = await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
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
    service, repository, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)
    registered = await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
    )
    session = next(iter(repository.sessions.values()))

    await service.logout(access_token=registered.tokens.access_token)

    assert repository.sessions[session.id].revoked_at is not None

    with pytest.raises(InvalidTokenError):
        await service.get_current_user(access_token=registered.tokens.access_token)


@pytest.mark.asyncio
async def test_get_current_user_returns_user_for_valid_access_token() -> None:
    service, _, mail_client = build_auth_service()
    code = await send_code_and_get_plain(service, mail_client)
    registered = await service.register(
        username="Hero",
        email="hero@example.com",
        password="Secret-pass1",
        verification_code=code,
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
