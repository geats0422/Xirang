from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.integrations.pageindex.runtime import launch_managed_pageindex


class FakePopen:
    def __init__(self, *_: Any, **__: Any) -> None:
        self.pid = 1234


def test_launch_managed_pageindex_prefers_configured_command(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_popen(command: Any, **kwargs: Any) -> FakePopen:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return FakePopen()

    settings = Settings(
        pageindex_url="http://localhost:8080",
        pageindex_launch_command="pageindex serve --host {host} --port {port} --log-level {log_level}",
        pageindex_launch_workdir="D:/pageindex",
        pageindex_launch_shell=True,
        pageindex_mock_fallback=False,
    )

    monkeypatch.setattr("app.integrations.pageindex.runtime.subprocess.Popen", fake_popen)

    process = launch_managed_pageindex(settings)

    assert process is not None
    assert captured["command"] == "pageindex serve --host localhost --port 8080 --log-level warning"
    assert captured["kwargs"]["cwd"] == "D:/pageindex"
    assert captured["kwargs"]["shell"] is True
    assert captured["kwargs"]["text"] is True
