from __future__ import annotations

import asyncio
import importlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MarkItDownClientError(RuntimeError):
    pass


@dataclass(slots=True)
class MarkItDownClient:
    enable_plugins: bool = False

    async def convert_to_markdown(self, *, file_name: str, file_bytes: bytes) -> str:
        return await asyncio.to_thread(self._convert_to_markdown_sync, file_name, file_bytes)

    def _convert_to_markdown_sync(self, file_name: str, file_bytes: bytes) -> str:
        try:
            module = importlib.import_module("markitdown")
            converter_class = module.MarkItDown
            converter = converter_class(enable_plugins=self.enable_plugins)
        except Exception as exc:
            raise MarkItDownClientError("MarkItDown is not available") from exc

        safe_name = _to_local_filename(file_name)
        try:
            with tempfile.TemporaryDirectory(prefix="xirang-markitdown-") as tmp_dir:
                input_path = Path(tmp_dir) / safe_name
                input_path.write_bytes(file_bytes)
                result = converter.convert(str(input_path))
        except Exception as exc:
            raise MarkItDownClientError(f"MarkItDown conversion failed: {exc}") from exc

        markdown = _extract_text_content(result)
        if not markdown.strip():
            raise MarkItDownClientError("MarkItDown returned empty markdown")
        return markdown


def _extract_text_content(result: Any) -> str:
    text_content = getattr(result, "text_content", None)
    if isinstance(text_content, str):
        return text_content
    if isinstance(result, str):
        return result
    return ""


def _to_local_filename(file_name: str) -> str:
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
