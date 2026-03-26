from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID


class AuthServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidCredentialsError(AuthServiceError):
    status_code = 401


class DuplicateIdentityError(AuthServiceError):
    status_code = 409


class InvalidTokenError(AuthServiceError):
    status_code = 401


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str


@dataclass(slots=True)
class AuthResult:
    user: Any
    tokens: TokenPair


@dataclass(slots=True)
class RefreshResult:
    tokens: TokenPair


class AuthRepositoryProtocol(Protocol):
    async def get_user_by_email(self, email_normalized: str) -> Any | None: ...

    async def get_user_by_username(self, username_normalized: str) -> Any | None: ...

    async def get_user_by_id(self, user_id: UUID) -> Any | None: ...

    async def create_user(
        self,
        *,
        username: str,
        username_normalized: str,
        email: str,
        email_normalized: str,
    ) -> Any: ...

    async def create_auth_credential(self, *, user_id: UUID, password_hash: str) -> Any: ...

    async def create_profile_for_user(self, *, user_id: UUID) -> Any: ...

    async def create_settings_for_user(self, *, user_id: UUID) -> Any: ...

    async def create_wallet_for_user(self, *, user_id: UUID) -> Any: ...

    async def get_auth_credential(self, user_id: UUID) -> Any | None: ...

    async def create_auth_session(
        self,
        *,
        user_id: UUID,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> Any: ...

    async def get_auth_session(self, session_id: UUID) -> Any | None: ...

    async def update_auth_session_tokens(
        self,
        *,
        session_id: UUID,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> Any: ...

    async def revoke_auth_session(self, *, session_id: UUID, revoked_at: datetime) -> Any: ...

    async def update_last_login(self, *, user_id: UUID, last_login_at: datetime) -> Any: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@dataclass(slots=True)
class AuthService:
    repository: AuthRepositoryProtocol
    password_service: Any
    token_service: Any

    async def register(self, username: str, email: str, password: str) -> AuthResult:
        email_normalized = email.lower().strip()
        username_normalized = username.lower().strip()

        if await self.repository.get_user_by_email(email_normalized):
            raise DuplicateIdentityError(f"Email already registered: {email}")
        if await self.repository.get_user_by_username(username_normalized):
            raise DuplicateIdentityError(f"Username already taken: {username}")

        from app.services.auth.passwords import PasswordValidationError

        try:
            self.password_service.validate_password(password)
        except PasswordValidationError as e:
            raise AuthServiceError(str(e)) from e

        password_hash = self.password_service.hash_password(password)
        user = await self.repository.create_user(
            username=username,
            username_normalized=username_normalized,
            email=email,
            email_normalized=email_normalized,
        )
        if user is None:
            raise AuthServiceError("Failed to create user")
        await self.repository.create_auth_credential(user_id=user.id, password_hash=password_hash)
        await self.repository.create_profile_for_user(user_id=user.id)
        await self.repository.create_settings_for_user(user_id=user.id)
        await self.repository.create_wallet_for_user(user_id=user.id)

        session_token = self.token_service.create_session_token()
        refresh_token_plain = self.token_service.create_session_token()
        session = await self.repository.create_auth_session(
            user_id=user.id,
            session_token_hash=self.token_service.hash_token(session_token),
            refresh_token_hash=self.token_service.hash_token(refresh_token_plain),
            expires_at=datetime.now(UTC)
            + timedelta(days=self.token_service.refresh_token_expire_days),
        )
        if session is None:
            raise AuthServiceError("Failed to create auth session")

        access_signed = self.token_service.build_access_token(
            user_id=user.id,
            session_id=session.id,
            session_token=session_token,
        )
        refresh_signed = self.token_service.build_refresh_token(
            user_id=user.id,
            session_id=session.id,
            session_token=session_token,
        )
        await self.repository.commit()
        return AuthResult(
            user=user,
            tokens=TokenPair(
                access_token=access_signed.token,
                refresh_token=refresh_signed.token,
            ),
        )

    async def login(self, identity: str, password: str) -> AuthResult:
        identity_normalized = identity.lower().strip()
        user = await self.repository.get_user_by_email(identity_normalized)
        if not user:
            user = await self.repository.get_user_by_username(identity_normalized)
        if not user:
            raise InvalidCredentialsError("Invalid credentials")

        credential = await self.repository.get_auth_credential(user.id)
        if not credential:
            raise InvalidCredentialsError("Invalid credentials")
        if not self.password_service.verify_password(
            plain_password=password,
            hashed_password=credential.password_hash,
        ):
            raise InvalidCredentialsError("Invalid credentials")

        await self.repository.update_last_login(user_id=user.id, last_login_at=datetime.now(UTC))

        session_token = self.token_service.create_session_token()
        refresh_token_plain = self.token_service.create_session_token()
        session = await self.repository.create_auth_session(
            user_id=user.id,
            session_token_hash=self.token_service.hash_token(session_token),
            refresh_token_hash=self.token_service.hash_token(refresh_token_plain),
            expires_at=datetime.now(UTC)
            + timedelta(days=self.token_service.refresh_token_expire_days),
        )
        if session is None:
            raise AuthServiceError("Failed to create auth session")

        access_signed = self.token_service.build_access_token(
            user_id=user.id,
            session_id=session.id,
            session_token=session_token,
        )
        refresh_signed = self.token_service.build_refresh_token(
            user_id=user.id,
            session_id=session.id,
            session_token=session_token,
        )
        await self.repository.commit()
        return AuthResult(
            user=user,
            tokens=TokenPair(
                access_token=access_signed.token,
                refresh_token=refresh_signed.token,
            ),
        )

    async def get_current_user(self, access_token: str) -> Any:
        try:
            payload = self.token_service.decode_token(
                access_token,
                expected_token_type="access",
            )
            session = await self.repository.get_auth_session(payload.session_id)
            if not session or session.revoked_at is not None:
                raise InvalidTokenError("Invalid token")
            user = await self.repository.get_user_by_id(payload.user_id)
            if not user:
                raise InvalidTokenError("User not found")
            return user
        except InvalidTokenError:
            raise
        except Exception as e:
            raise InvalidTokenError(str(e)) from e

    async def logout(self, access_token: str) -> None:
        try:
            payload = self.token_service.decode_token(
                access_token,
                expected_token_type="access",
            )
        except Exception:
            return

        session = await self.repository.get_auth_session(payload.session_id)
        if session:
            await self.repository.revoke_auth_session(
                session_id=payload.session_id,
                revoked_at=datetime.now(UTC),
            )
            await self.repository.commit()

    async def refresh(self, refresh_token: str) -> RefreshResult:
        try:
            payload = self.token_service.decode_token(
                refresh_token,
                expected_token_type="refresh",
            )
            session = await self.repository.get_auth_session(payload.session_id)
            if not session:
                raise InvalidTokenError("Invalid refresh token")
            if session.session_token_hash != self.token_service.hash_token(payload.session_token):
                raise InvalidTokenError("Invalid refresh token")

            session_token = self.token_service.create_session_token()
            refresh_token_plain = self.token_service.create_session_token()
            await self.repository.update_auth_session_tokens(
                session_id=payload.session_id,
                session_token_hash=self.token_service.hash_token(session_token),
                refresh_token_hash=self.token_service.hash_token(refresh_token_plain),
                expires_at=datetime.now(UTC)
                + timedelta(days=self.token_service.refresh_token_expire_days),
            )
            access_signed = self.token_service.build_access_token(
                user_id=payload.user_id,
                session_id=payload.session_id,
                session_token=session_token,
            )
            refresh_signed = self.token_service.build_refresh_token(
                user_id=payload.user_id,
                session_id=payload.session_id,
                session_token=session_token,
            )
            await self.repository.commit()
            return RefreshResult(
                tokens=TokenPair(
                    access_token=access_signed.token,
                    refresh_token=refresh_signed.token,
                )
            )
        except InvalidTokenError:
            raise
        except Exception as e:
            raise InvalidTokenError(str(e)) from e
