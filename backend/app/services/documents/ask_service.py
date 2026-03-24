"""Ask service for document Q&A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


@dataclass
class AskResponse:
    question: str = ""
    answer: str = ""
    sources: list[str] | None = None
    source_chunks: list[dict[str, object]] | None = None
    confidence: float | None = None


class AskService:
    """Service for answering questions about documents."""

    def __init__(self) -> None:
        return None

    async def ask(self, question: str, document_id: UUID, context_chunks: int = 5) -> AskResponse:
        return AskResponse(
            question=question,
            answer="Answer",
            sources=[],
            source_chunks=[],
            confidence=1.0,
        )
