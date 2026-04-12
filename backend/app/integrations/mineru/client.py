from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


class MinerUClientError(RuntimeError):
    pass


@dataclass(slots=True)
class MinerUClient:
    base_url: str
    timeout_seconds: float = 300.0
    backend: str = "hybrid-auto-engine"
    lang_list: tuple[str, ...] = ("ch",)

    async def parse_to_markdown(
        self,
        *,
        file_name: str,
        file_bytes: bytes,
        backend: str | None = None,
        lang_list: Sequence[str] | None = None,
    ) -> str:
        endpoint = f"{self.base_url.rstrip('/')}/file_parse"
        selected_backend = backend or self.backend
        selected_langs = tuple(lang_list) if lang_list else self.lang_list

        data: dict[str, str] = {
            "backend": selected_backend,
            "return_md": "true",
            "return_middle_json": "false",
            "return_model_output": "false",
            "return_content_list": "false",
            "return_images": "false",
            "response_format_zip": "false",
            "lang_list": ",".join(selected_langs),
        }

        multipart_file_name = _to_multipart_filename(file_name)
        files = {"files": (multipart_file_name, file_bytes, "application/octet-stream")}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(endpoint, data=data, files=files)
        except httpx.TimeoutException as exc:
            raise MinerUClientError(
                f"MinerU parse timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.HTTPError as exc:
            raise MinerUClientError(f"MinerU request failed: {exc}") from exc

        if response.status_code >= 400:
            raise MinerUClientError(
                f"MinerU parse failed: status={response.status_code}, body={response.text[:500]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MinerUClientError("MinerU response is not valid JSON") from exc

        markdown = _extract_markdown(payload)
        if not markdown.strip():
            raise MinerUClientError("MinerU returned empty markdown")
        return markdown

    async def health_check(self) -> bool:
        endpoint = f"{self.base_url.rstrip('/')}/health"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(endpoint)
            return response.status_code < 400
        except Exception:
            return False


def _extract_markdown(payload: Any) -> str:
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, dict):
            for item in results.values():
                if not isinstance(item, dict):
                    continue
                md_content = item.get("md_content")
                if isinstance(md_content, str):
                    return md_content

        for key in ("markdown", "md"):
            raw = payload.get(key)
            if isinstance(raw, str):
                return raw

        data = payload.get("data")
        if isinstance(data, dict):
            nested = _extract_markdown(data)
            if nested:
                return nested

        result = payload.get("result")
        if isinstance(result, dict):
            nested = _extract_markdown(result)
            if nested:
                return nested

    return ""


def _to_multipart_filename(file_name: str) -> str:
    candidate = file_name.strip()
    if not candidate:
        return "document.bin"

    path = Path(candidate)
    stem = path.stem or "document"
    suffix = path.suffix or ".bin"

    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "document"
    safe_suffix = re.sub(r"[^A-Za-z0-9._-]+", "", suffix)
    if not safe_suffix.startswith("."):
        safe_suffix = f".{safe_suffix}" if safe_suffix else ".bin"

    return f"{safe_stem}{safe_suffix}"
