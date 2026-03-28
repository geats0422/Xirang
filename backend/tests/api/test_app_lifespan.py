from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

if TYPE_CHECKING:
    from fastapi import FastAPI


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


def test_create_app_lifespan_starts_and_stops_managed_pageindex(
    monkeypatch,
) -> None:
    fake_process = FakeProcess()

    async def fake_ensure_pageindex_ready_with_launch(
        settings: object,
    ) -> tuple[bool, FakeProcess | None]:
        _ = settings
        return True, fake_process

    monkeypatch.setattr(
        "app.main.ensure_pageindex_ready_with_launch",
        fake_ensure_pageindex_ready_with_launch,
    )

    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        app = cast("FastAPI", client.app)
        assert app.state.pageindex_process is fake_process

    assert fake_process.terminated is True
    assert fake_process.waited is True
    assert fake_process.killed is False


def test_create_app_lifespan_raises_when_pageindex_never_becomes_ready(
    monkeypatch,
) -> None:
    async def fake_ensure_pageindex_ready_with_launch(settings: object) -> tuple[bool, None]:
        _ = settings
        return False, None

    monkeypatch.setattr(
        "app.main.ensure_pageindex_ready_with_launch",
        fake_ensure_pageindex_ready_with_launch,
    )

    with (
        pytest.raises(RuntimeError, match="PageIndex did not become ready"),
        TestClient(create_app()),
    ):
        pass
