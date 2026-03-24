from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

import asyncpg
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def load_backend_helpers() -> tuple[
    Callable[[], Any], Callable[..., str], Callable[[str], str]
]:
    from app.core.config import get_settings
    from app.db.session import build_admin_database_url, build_async_database_url

    return get_settings, build_admin_database_url, build_async_database_url


def to_asyncpg_dsn(database_url: str) -> str:
    url = make_url(database_url)

    if url.drivername == "postgresql+asyncpg":
        url = url.set(drivername="postgresql")

    return url.render_as_string(hide_password=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize the local PostgreSQL database."
    )
    parser.add_argument("--database-url", dest="database_url")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--skip-vector-extension", action="store_true")
    return parser.parse_args()


def quote_identifier(value: str) -> str:
    return value.replace('"', '""')


async def create_database_if_needed(database_url: str, reset: bool) -> None:
    _, build_admin_database_url, build_async_database_url = load_backend_helpers()
    target_url = make_url(build_async_database_url(database_url))
    admin_url = build_admin_database_url(database_url)
    database_name = target_url.database

    if database_name is None:
        raise ValueError("DATABASE_URL must include a database name")

    connection = await asyncpg.connect(to_asyncpg_dsn(admin_url))

    try:
        if reset:
            await connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()",
                database_name,
            )
            await connection.execute(
                f'DROP DATABASE IF EXISTS "{quote_identifier(database_name)}"'
            )

        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database_name,
        )

        if not exists:
            await connection.execute(
                f'CREATE DATABASE "{quote_identifier(database_name)}"'
            )
    finally:
        await connection.close()


async def ensure_vector_extension(database_url: str) -> None:
    _, _, build_async_database_url = load_backend_helpers()
    connection = await asyncpg.connect(
        to_asyncpg_dsn(build_async_database_url(database_url))
    )

    try:
        await connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except asyncpg.FeatureNotSupportedError as exc:
        raise RuntimeError(
            "pgvector is not installed on this PostgreSQL instance. "
            "Install the extension or rerun init_db.py with --skip-vector-extension."
        ) from exc
    finally:
        await connection.close()


def run_alembic_upgrade() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(BACKEND_ROOT / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=REPO_ROOT,
        check=True,
    )


async def main() -> None:
    args = parse_args()
    get_settings, _, _ = load_backend_helpers()
    database_url = args.database_url or get_settings().database_url

    await create_database_if_needed(database_url, reset=args.reset)

    if not args.skip_vector_extension:
        await ensure_vector_extension(database_url)

    if not args.skip_migrations:
        run_alembic_upgrade()


if __name__ == "__main__":
    asyncio.run(main())
