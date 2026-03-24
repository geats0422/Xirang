from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.api.v1.auth import get_auth_service
from app.core.config import get_settings
from app.repositories.auth_repository import AuthRepository
from app.services.auth.service import AuthService


@pytest.mark.asyncio
async def test_get_auth_service_returns_real_service_instance() -> None:
    fake_session = AsyncMock()

    service = await get_auth_service(session=fake_session)

    assert isinstance(service, AuthService)
    assert isinstance(service.repository, AuthRepository)


@pytest.mark.asyncio
async def test_get_auth_service_uses_runtime_token_settings() -> None:
    fake_session = AsyncMock()
    settings = get_settings()

    service = await get_auth_service(session=fake_session)

    assert service.token_service.access_token_expire_minutes == settings.access_token_expire_minutes
    assert service.token_service.refresh_token_expire_days == settings.refresh_token_expire_days
