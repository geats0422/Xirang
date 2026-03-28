"""Text normalization utilities for document processing."""
from __future__ import annotations

import re


def strip_markdown(raw: str) -> str:
    """Remove common markdown syntax from document content for clean question generation."""
    if not raw:
        return ""

    # Remove link syntax but keep link text: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"", raw)

    # Remove image syntax: ![alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"", text)

    # Remove heading markers from start of lines (up to 6 #)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)

    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"", text)

    # Remove strikethrough
    text = re.sub(r"~~([^~]+)~~", r"", text)

    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"", text)

    # Remove horizontal rules
    text = re.sub(r"(?m)^[-*_]{3,}\s*$", "", text)

    # Normalize whitespace
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return " ".join(cleaned_lines)
