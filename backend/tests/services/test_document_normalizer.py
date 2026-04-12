from __future__ import annotations

from app.services.documents.normalizer import normalize_markdown


def test_normalize_markdown_cleans_line_endings_and_heading_spacing() -> None:
    raw = "\ufeff#Title\r\n\r\n\r\n• item\r\ntext\x00"

    normalized = normalize_markdown(raw)

    assert normalized == "# Title\n\n- item\ntext\n"


def test_normalize_markdown_returns_empty_when_input_empty() -> None:
    assert normalize_markdown("") == ""
