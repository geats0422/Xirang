import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.session import (
    build_admin_database_url,
    build_async_database_url,
    create_async_engine_from_settings,
    create_session_factory,
)


def test_build_async_database_url_adds_asyncpg_driver() -> None:
    url = build_async_database_url("postgresql://user:pass@localhost:5432/xirang")

    assert url == "postgresql+asyncpg://user:pass@localhost:5432/xirang"


def test_build_async_database_url_preserves_asyncpg_driver() -> None:
    url = build_async_database_url("postgresql+asyncpg://user:pass@localhost:5432/xirang")

    assert url == "postgresql+asyncpg://user:pass@localhost:5432/xirang"


def test_build_admin_database_url_switches_database_name() -> None:
    url = build_admin_database_url(
        "postgresql+asyncpg://user:pass@localhost:5432/xirang",
        admin_database="postgres",
    )

    assert url == "postgresql+asyncpg://user:pass@localhost:5432/postgres"


def test_create_async_engine_from_settings_uses_async_url() -> None:
    settings = Settings(database_url="postgresql://user:pass@localhost:5432/xirang")
    engine = create_async_engine_from_settings(settings)

    try:
        assert isinstance(engine, AsyncEngine)
        assert str(engine.url) == "postgresql+asyncpg://user:***@localhost:5432/xirang"
    finally:
        asyncio.run(engine.dispose())


def test_create_session_factory_returns_async_sessionmaker() -> None:
    settings = Settings(database_url="postgresql://user:pass@localhost:5432/xirang")
    engine = create_async_engine_from_settings(settings)

    try:
        session_factory = create_session_factory(engine)
        session = session_factory()

        assert isinstance(session_factory, async_sessionmaker)
        assert isinstance(session, AsyncSession)
    finally:
        asyncio.run(engine.dispose())
