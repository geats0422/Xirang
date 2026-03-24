from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel


@dataclass(slots=True)
class SignedToken:
    token: str
    expires_at: datetime


class TokenPayload(BaseModel):
    sub: str
    sid: str
    typ: str
    sst: str
    exp: int

    @property
    def user_id(self) -> UUID:
        return UUID(self.sub)

    @property
    def session_id(self) -> UUID:
        return UUID(self.sid)

    @property
    def session_token(self) -> str:
        return self.sst


class TokenService:
    def __init__(
        self,
        *,
        secret_key: str,
        access_token_expire_minutes: int,
        refresh_token_expire_days: int,
        algorithm: str = "HS256",
    ) -> None:
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.algorithm = algorithm

    def build_access_token(
        self, *, user_id: UUID, session_id: UUID, session_token: str
    ) -> SignedToken:
        expires_at = datetime.now(tz=UTC) + timedelta(minutes=self.access_token_expire_minutes)
        return SignedToken(
            token=self._encode_token(
                user_id=user_id,
                session_id=session_id,
                session_token=session_token,
                token_type="access",
                expires_at=expires_at,
            ),
            expires_at=expires_at,
        )

    def build_refresh_token(
        self, *, user_id: UUID, session_id: UUID, session_token: str
    ) -> SignedToken:
        expires_at = datetime.now(tz=UTC) + timedelta(days=self.refresh_token_expire_days)
        return SignedToken(
            token=self._encode_token(
                user_id=user_id,
                session_id=session_id,
                session_token=session_token,
                token_type="refresh",
                expires_at=expires_at,
            ),
            expires_at=expires_at,
        )

    def create_session_token(self) -> str:
        return token_urlsafe(32)

    def decode_token(self, token: str, *, expected_token_type: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_payload = TokenPayload.model_validate(payload)
        except (JWTError, ValueError) as exc:
            raise ValueError("Invalid token") from exc

        if token_payload.typ != expected_token_type:
            raise ValueError("Invalid token type")

        return token_payload

    @staticmethod
    def hash_token(value: str) -> str:
        return sha256(value.encode("utf-8")).hexdigest()

    def _encode_token(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        session_token: str,
        token_type: str,
        expires_at: datetime,
    ) -> str:
        return jwt.encode(
            {
                "sub": str(user_id),
                "sid": str(session_id),
                "typ": token_type,
                "sst": session_token,
                "exp": int(expires_at.timestamp()),
            },
            self.secret_key,
            algorithm=self.algorithm,
        )
