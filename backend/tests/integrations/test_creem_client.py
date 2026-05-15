import httpx
import pytest

from app.integrations.creem.client import CreemApiClient, CreemApiError, CreemApiTimeoutError

pytestmark = pytest.mark.asyncio(loop_scope="module")


async def test_create_checkout_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method, url, json=None, headers=None):  # type: ignore[no-untyped-def]
        return httpx.Response(200, json={"checkout_url": "https://checkout.test"})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    client = CreemApiClient(base_url="https://api.creem.io", api_key="test")
    data = await client.create_checkout({"a": 1})
    assert data["checkout_url"] == "https://checkout.test"


async def test_create_checkout_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method, url, json=None, headers=None):  # type: ignore[no-untyped-def]
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    client = CreemApiClient(base_url="https://api.creem.io", api_key="test")
    with pytest.raises(CreemApiTimeoutError):
        await client.create_checkout({"a": 1})


async def test_create_checkout_4xx(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method, url, json=None, headers=None):  # type: ignore[no-untyped-def]
        return httpx.Response(400, json={"error": "bad"})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    client = CreemApiClient(base_url="https://api.creem.io", api_key="test")
    with pytest.raises(CreemApiError):
        await client.create_checkout({"a": 1})
