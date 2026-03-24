from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class PageIndexConfig:
    base_url: str
    timeout_seconds: int = 30
    api_key: str | None = None


@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    content: str
    score: float
    chapter: str | None = None
    page: int | None = None


@dataclass(slots=True)
class AskResult:
    answer: str
    source_chunks: list[dict[str, object]]
    confidence: float


@dataclass(slots=True)
class ChapterRecommendation:
    chapter: str
    reason: str
    next_step: str


@dataclass(slots=True)
class QuestionSuggestion:
    question_id: str
    reason: str


@dataclass(slots=True)
class RecommendationResult:
    weak_chapters: list[ChapterRecommendation]
    suggested_questions: list[QuestionSuggestion]


@dataclass(slots=True)
class IndexDocumentResult:
    status: str
    document_id: str


class PageIndexClientProtocol(Protocol):
    async def index_document(
        self,
        *,
        document_id: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]: ...

    async def search(
        self,
        *,
        document_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, object]]: ...

    async def ask(
        self,
        *,
        document_id: str,
        question: str,
        context_chunks: int = 3,
    ) -> dict[str, object]: ...

    async def get_study_recommendation(
        self,
        *,
        document_id: str,
        user_id: str,
    ) -> dict[str, object]: ...


class PageIndexBackend:
    def __init__(self, *, client: PageIndexClientProtocol, config: PageIndexConfig) -> None:
        self.client = client
        self.config = config

    async def index_document(self, *, document_id: str, content: str) -> IndexDocumentResult:
        raw = await self.client.index_document(document_id=document_id, content=content)
        return IndexDocumentResult(
            status=str(raw.get("status", "indexed")),
            document_id=str(raw.get("document_id", document_id)),
        )

    async def search(self, *, document_id: str, query: str, top_k: int = 5) -> list[SearchResult]:
        raw_results = await self.client.search(document_id=document_id, query=query, top_k=top_k)

        def to_float(value: Any) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        def to_int(value: Any) -> int | None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return [
            SearchResult(
                chunk_id=str(item.get("chunk_id", "")),
                content=str(item.get("content", "")),
                score=to_float(item.get("score", 0.0)),
                chapter=str(item.get("chapter")) if item.get("chapter") is not None else None,
                page=to_int(item.get("page")),
            )
            for item in raw_results[:top_k]
        ]

    async def ask(self, *, document_id: str, question: str, context_chunks: int = 3) -> AskResult:
        raw = await self.client.ask(
            document_id=document_id,
            question=question,
            context_chunks=context_chunks,
        )
        source_chunks_raw = raw.get("source_chunks")
        source_chunks = source_chunks_raw if isinstance(source_chunks_raw, list) else []

        confidence_raw: Any = raw.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        return AskResult(
            answer=str(raw.get("answer", "")),
            source_chunks=source_chunks,
            confidence=confidence,
        )

    async def get_study_recommendation(
        self,
        *,
        document_id: str,
        user_id: str,
    ) -> RecommendationResult:
        raw = await self.client.get_study_recommendation(document_id=document_id, user_id=user_id)

        weak_raw = raw.get("weak_chapters")
        weak_items = weak_raw if isinstance(weak_raw, list) else []
        weak_chapters = [
            ChapterRecommendation(
                chapter=str(item.get("chapter", "")),
                reason=str(item.get("reason", "")),
                next_step=str(item.get("next_step", "")),
            )
            for item in weak_items
        ]

        suggested_raw = raw.get("suggested_questions")
        suggested_items = suggested_raw if isinstance(suggested_raw, list) else []
        suggested_questions = [
            QuestionSuggestion(
                question_id=str(item.get("question_id", "")),
                reason=str(item.get("reason", "")),
            )
            for item in suggested_items
        ]

        return RecommendationResult(
            weak_chapters=weak_chapters,
            suggested_questions=suggested_questions,
        )
