from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CreemApiError(Exception):
    pass


class CreemApiTimeoutError(CreemApiError):
    pass


class CreemApiClient:
    def __init__(self, *, base_url: str, api_key: str, timeout_seconds: float = 10.0) -> None:
        if api_key.startswith("creem_test_"):
            self.base_url = "https://test-api.creem.io"
        else:
            self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def create_checkout(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/v1/checkouts", payload)

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v1/subscriptions/{subscription_id}")

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/v1/subscriptions/{subscription_id}/cancel")

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    json=payload,
                    headers={"x-api-key": self.api_key},
                )
        except httpx.TimeoutException as exc:
            raise CreemApiTimeoutError("Creem request timeout") from exc
        except httpx.HTTPError as exc:
            raise CreemApiError("Creem request failed") from exc

        if response.status_code >= 400:
            error_body = response.text
            logger.error("Creem API error: %s %s -> %s %s", method, path, response.status_code, error_body)
            raise CreemApiError(f"Creem request failed with status {response.status_code}: {error_body}")
        return dict(response.json())
