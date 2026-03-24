from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class PageIndexClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self._base_url = (base_url or get_settings().pageindex_url).rstrip("/")
        self._timeout = timeout_seconds

    async def _request(
        self,
        *,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(method, url, json=json)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            return {}

    async def index_document(
        self,
        *,
        document_id: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path=f"/documents/{document_id}/index",
            json={
                "content": content,
                "metadata": metadata or {},
            },
        )

    async def search(
        self,
        *,
        document_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        result = await self._request(
            method="POST",
            path=f"/documents/{document_id}/search",
            json={
                "query": query,
                "top_k": top_k,
            },
        )
        results = result.get("results", [])
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        return []

    async def ask(
        self,
        *,
        document_id: str,
        question: str,
        context_chunks: int = 3,
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path=f"/documents/{document_id}/ask",
            json={
                "question": question,
                "context_chunks": context_chunks,
            },
        )

    async def get_study_recommendation(
        self,
        *,
        document_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            path=f"/documents/{document_id}/recommendations/{user_id}",
        )

    async def delete_document(
        self,
        *,
        document_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="DELETE",
            path=f"/documents/{document_id}",
        )

    async def health_check(self) -> bool:
        try:
            await self._request(method="GET", path="/health")
            return True
        except Exception:
            return False
