from __future__ import annotations

import re

_MULTI_BLANK_LINES = re.compile(r"\n{3,}")
_TRAILING_SPACES = re.compile(r"[ \t]+$")
_HEADING_WITHOUT_SPACE = re.compile(r"^(#{1,6})([^\s#])", re.MULTILINE)
_UNICODE_BULLETS = re.compile(r"^[ \t]*[•·●◦]\s+", re.MULTILINE)


def normalize_markdown(raw_markdown: str) -> str:
    if not raw_markdown:
        return ""

    content = raw_markdown.replace("\r\n", "\n").replace("\r", "\n")
    content = content.replace("\ufeff", "")
    content = content.replace("\x00", "")
    content = _HEADING_WITHOUT_SPACE.sub(r"\1 \2", content)
    content = _UNICODE_BULLETS.sub("- ", content)

    lines = [_TRAILING_SPACES.sub("", line) for line in content.split("\n")]
    content = "\n".join(lines)
    content = _MULTI_BLANK_LINES.sub("\n\n", content)
    content = content.strip()

    if not content:
        return ""
    return f"{content}\n"
