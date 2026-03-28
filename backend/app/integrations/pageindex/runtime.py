from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from app.integrations.pageindex.client import PageIndexClient

if TYPE_CHECKING:
    from app.core.config import Settings

LOCAL_PAGEINDEX_HOSTS = {"127.0.0.1", "localhost"}


def _parse_pageindex_endpoint(pageindex_url: str) -> tuple[str, int] | None:
    parsed = urlparse(pageindex_url)
    hostname = parsed.hostname
    if hostname is None:
        return None

    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    return hostname, port


def should_manage_pageindex(settings: Settings) -> bool:
    if not settings.pageindex_auto_start:
        return False

    endpoint = _parse_pageindex_endpoint(settings.pageindex_url)
    if endpoint is None:
        return False

    hostname, _ = endpoint
    return hostname in LOCAL_PAGEINDEX_HOSTS


def _format_launch_command(settings: Settings, *, host: str, port: int) -> str | None:
    launch_command = settings.pageindex_launch_command
    if launch_command is None:
        return None

    normalized = launch_command.strip()
    if not normalized:
        return None

    return normalized.format(
        host=host,
        port=port,
        url=settings.pageindex_url,
        log_level=settings.pageindex_subprocess_log_level.lower(),
    )


async def wait_for_pageindex(
    *, client: PageIndexClient, timeout_seconds: float, interval_seconds: float
) -> bool:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        if await client.health_check():
            return True
        await asyncio.sleep(interval_seconds)
    return await client.health_check()


async def ensure_pageindex_ready(settings: Settings) -> bool:
    client = PageIndexClient(
        base_url=settings.pageindex_url, timeout_seconds=settings.pageindex_timeout_seconds
    )
    return await wait_for_pageindex(
        client=client,
        timeout_seconds=settings.pageindex_startup_timeout_seconds,
        interval_seconds=settings.pageindex_startup_poll_interval_seconds,
    )


async def ensure_pageindex_ready_with_launch(
    settings: Settings,
) -> tuple[bool, subprocess.Popen[str] | None]:
    pageindex_ready = await ensure_pageindex_ready(settings)
    if pageindex_ready:
        return True, None

    if not should_manage_pageindex(settings):
        return False, None

    managed_process = launch_managed_pageindex(settings)
    if managed_process is None:
        return False, None

    pageindex_ready = await ensure_pageindex_ready(settings)
    if pageindex_ready:
        return True, managed_process

    if managed_process.poll() is None:
        managed_process.terminate()
        managed_process.wait(timeout=5)
    return False, managed_process


def launch_managed_pageindex(settings: Settings) -> subprocess.Popen[str] | None:
    endpoint = _parse_pageindex_endpoint(settings.pageindex_url)
    if endpoint is None:
        return None

    host, port = endpoint
    backend_root = Path(__file__).resolve().parents[3]
    configured_command = _format_launch_command(settings, host=host, port=port)
    launch_cwd = settings.pageindex_launch_workdir or str(backend_root)

    if configured_command is not None:
        return subprocess.Popen(
            configured_command,
            cwd=launch_cwd,
            shell=settings.pageindex_launch_shell,
            text=True,
        )

    if not settings.pageindex_mock_fallback:
        return None

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "mock_pageindex_server:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        settings.pageindex_subprocess_log_level.lower(),
    ]
    return subprocess.Popen(command, cwd=launch_cwd, text=True)
