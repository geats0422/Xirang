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
async def test_mineru_client_parse_to_markdown_supports_results_md_content(monkeypatch) -> None:
    class ResultsPayloadClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            _ = args
            _ = kwargs
            return FakeResponse(
                200,
                payload={"results": {"sample": {"md_content": "# from-results"}}},
            )

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", ResultsPayloadClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    markdown = await client.parse_to_markdown(file_name="doc.pdf", file_bytes=b"binary")

    assert markdown == "# from-results"


@pytest.mark.asyncio
async def test_mineru_client_parse_to_markdown_sanitizes_unicode_filename(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class CaptureFilenameClient(FakeAsyncClient):
        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            captured.update(kwargs)
            return FakeResponse(200, payload={"markdown": "# ok"})

    monkeypatch.setattr("app.integrations.mineru.client.httpx.AsyncClient", CaptureFilenameClient)
    client = MinerUClient(base_url="http://127.0.0.1:8300")

    await client.parse_to_markdown(
        file_name="13、-AI行业落地案例补充知识.pdf", file_bytes=b"binary"
    )

    files = captured.get("files")
    assert isinstance(files, dict)
    file_tuple = files.get("files")
    assert isinstance(file_tuple, tuple)
    assert len(file_tuple) == 3
    sent_name = file_tuple[0]
    assert isinstance(sent_name, str)
    assert sent_name.endswith(".pdf")
    assert all(ord(char) < 128 for char in sent_name)


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
