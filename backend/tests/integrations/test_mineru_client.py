from __future__ import annotations

from typing import Any

import pytest

from app.integrations.mineru.client import MinerUClient, MinerUClientError


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict[str, Any] | None = None,
        *,
        json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = "response-body"
        self._json_error = json_error

    def json(self) -> dict[str, Any]:
        if self._json_error:
            raise ValueError("invalid json")
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        _ = args
        _ = kwargs

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = exc_type
        _ = exc
        _ = tb

    async def post(self, *args: object, **kwargs: object) -> FakeResponse:
        _ = args
        _ = kwargs
        return FakeResponse(200, payload={"markdown": "# title\n\ncontent"})

    async def get(self, *args: object, **kwargs: object) -> FakeResponse:
        _ = args
        _ = kwargs
        return FakeResponse(200, payload={"ok": True})


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_success(monkeypatch) -> None:
    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", FakeAsyncClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    markdown = await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")

    assert markdown.startswith("# title")


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_raises_on_empty_markdown(monkeypatch) -> None:
    class EmptyMarkdownClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            _ = args
            _ = kwargs
            return FakeResponse(200, payload={"markdown": ""})

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", EmptyMarkdownClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    with pytest.raises(MinerUClientError):
        await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_supports_nested_data(monkeypatch) -> None:
    class NestedDataClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            _ = args
            _ = kwargs
            return FakeResponse(200, payload={"data": {"markdown": "# nested"}})

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", NestedDataClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    markdown = await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")

    assert markdown == "# nested"


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_supports_nested_result(monkeypatch) -> None:
    class NestedResultClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            _ = args
            _ = kwargs
            return FakeResponse(200, payload={"result": {"md": "# nested-result"}})

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", NestedResultClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    markdown = await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")

    assert markdown == "# nested-result"


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_raises_on_http_error(monkeypatch) -> None:
    class HttpErrorClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            _ = args
            _ = kwargs
            return FakeResponse(500, payload={"message": "error"})

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", HttpErrorClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    with pytest.raises(MinerUClientError, match="status=500"):
        await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_raises_on_invalid_json(monkeypatch) -> None:
    class InvalidJsonClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            _ = args
            _ = kwargs
            return FakeResponse(200, json_error=True)

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", InvalidJsonClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    with pytest.raises(MinerUClientError, match="not valid JSON"):
        await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")
