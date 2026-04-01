from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

from app.core.config import Settings, get_settings
from app.integrations.pageindex.client import PageIndexClient


class PageIndexLauncher:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = PageIndexClient(
            base_url=self._settings.pageindex_url,
            timeout_seconds=self._settings.pageindex_timeout_seconds,
        )
        self._process: asyncio.subprocess.Process | None = None
        self._startup_lock = self._resolve_lock_path()

    async def health_check(self) -> bool:
        return await self._client.health_check()

    async def ensure_started(self) -> bool:
        if await self.health_check():
            return True
        if not self._settings.pageindex_auto_start:
            return False
        if not self._settings.pageindex_launch_command:
            return False

        acquired = self._acquire_startup_lock()
        if not acquired:
            return await self._wait_until_healthy()

        try:
            if await self.health_check():
                return True
            await self._start_process()
            return await self._wait_until_healthy()
        finally:
            self._release_startup_lock()

    async def stop(self) -> None:
        if self._process is None or self._process.returncode is not None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()

    async def _start_process(self) -> None:
        command = self._settings.pageindex_launch_command
        if not command:
            return
        workdir = self._settings.pageindex_launch_workdir or None
        if self._settings.pageindex_launch_shell:
            self._process = await asyncio.create_subprocess_shell(
                command,
                cwd=workdir,
            )
            return
        args = self._split_command(command)
        if not args:
            return
        self._process = await asyncio.create_subprocess_exec(
            *args,
            cwd=workdir,
        )

    async def _wait_until_healthy(self) -> bool:
        timeout = max(1, self._settings.pageindex_startup_timeout_seconds)
        interval = max(0.2, self._settings.pageindex_startup_poll_interval_seconds)
        attempts = max(1, int(timeout / interval))
        for _ in range(attempts):
            if await self.health_check():
                return True
            await asyncio.sleep(interval)
        return await self.health_check()

    def _resolve_lock_path(self) -> Path:
        upload_dir = Path(self._settings.upload_dir)
        base_dir = upload_dir.parent if upload_dir.name else upload_dir
        return base_dir / 'pageindex-autostart.lock'

    def _acquire_startup_lock(self) -> bool:
        self._startup_lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self._startup_lock), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            return False
        os.close(fd)
        return True

    def _release_startup_lock(self) -> None:
        with suppress(FileNotFoundError):
            self._startup_lock.unlink()

    @staticmethod
    def _split_command(command: str) -> Sequence[str]:
        import shlex

        return shlex.split(command, posix=False)


def create_pageindex_launcher(settings: Settings | None = None) -> PageIndexLauncher:
    return PageIndexLauncher(settings)
