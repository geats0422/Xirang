from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def build_async_database_url(database_url: str) -> str:
    url = make_url(database_url)
    drivername = url.drivername

    if drivername == "postgresql" or (
        drivername.startswith("postgresql+") and drivername != "postgresql+asyncpg"
    ):
        drivername = "postgresql+asyncpg"

    return url.set(drivername=drivername).render_as_string(hide_password=False)


def build_admin_database_url(database_url: str, admin_database: str = "postgres") -> str:
    url = make_url(build_async_database_url(database_url))
    return url.set(database=admin_database).render_as_string(hide_password=False)


def create_async_engine_from_settings(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        build_async_database_url(settings.database_url),
        echo=settings.database_echo,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine_from_settings(get_settings())


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_engine())


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
