from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from app.workers.main import run_worker


@dataclass
class FakeProcess:
    terminated: bool = False
    waited: bool = False
    killed: bool = False
    running: bool = True

    def poll(self) -> None | int:
        return None if self.running else 0

    def terminate(self) -> None:
        self.terminated = True
        self.running = False

    def wait(self, timeout: int | float | None = None) -> int:
        _ = timeout
        self.waited = True
        return 0

    def kill(self) -> None:
        self.killed = True
        self.running = False


class FakeSessionFactory:
    def __call__(self) -> FakeSessionFactory:
        return self

    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = exc_type
        _ = exc
        _ = tb


class FakeRunner:
    def __init__(
        self,
        repository: object,
        registry: object,
        signal_handler: list[Callable[[int, object | None], None] | None],
    ) -> None:
        _ = repository
        _ = registry
        self._signal_handler = signal_handler
        self._called = False

    async def run_one(self, queue_name: str) -> bool:
        _ = queue_name
        if not self._called:
            self._called = True
            handler = self._signal_handler[0]
            if handler is not None:
                handler(0, None)
        return False


@pytest.mark.asyncio
async def test_run_worker_raises_when_pageindex_not_ready(monkeypatch) -> None:
    async def fake_ensure_pageindex_ready_with_launch(settings: object) -> tuple[bool, None]:
        _ = settings
        return False, None

    monkeypatch.setattr(
        "app.workers.main.ensure_pageindex_ready_with_launch",
        fake_ensure_pageindex_ready_with_launch,
    )

    with pytest.raises(RuntimeError, match="PageIndex is not ready"):
        await run_worker(queue_name="default", poll_interval=0)


@pytest.mark.asyncio
async def test_run_worker_cleans_up_managed_pageindex_process(
    monkeypatch,
) -> None:
    fake_process = FakeProcess()
    signal_handler: list[Callable[[int, object | None], None] | None] = [None]

    async def fake_ensure_pageindex_ready_with_launch(settings: object) -> tuple[bool, FakeProcess]:
        _ = settings
        return True, fake_process

    def fake_signal(signum: int, handler: Callable[[int, object | None], None]) -> None:
        _ = signum
        signal_handler[0] = handler

    monkeypatch.setattr(
        "app.workers.main.ensure_pageindex_ready_with_launch",
        fake_ensure_pageindex_ready_with_launch,
    )
    monkeypatch.setattr("app.workers.main.build_job_registry", lambda: object())
    monkeypatch.setattr("app.workers.main.get_session_factory", lambda: FakeSessionFactory())
    monkeypatch.setattr("app.workers.main.DocumentRepository", lambda session: object())
    monkeypatch.setattr("app.workers.main.WorkerJobRepository", lambda repo: object())
    monkeypatch.setattr("app.workers.main.signal.signal", fake_signal)

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("app.workers.main.asyncio.sleep", fake_sleep)

    def fake_runner_factory(repository: object, registry: object) -> FakeRunner:
        return FakeRunner(repository=repository, registry=registry, signal_handler=signal_handler)

    monkeypatch.setattr("app.workers.main.JobRunner", fake_runner_factory)

    await run_worker(queue_name="default", poll_interval=0)

    assert fake_process.terminated is True
    assert fake_process.waited is True
    assert fake_process.killed is False
