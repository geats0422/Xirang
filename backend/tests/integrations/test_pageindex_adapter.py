from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.retrieval.pageindex_backend import (
    PageIndexBackend,
    PageIndexConfig,
    SearchResult,
)


class MockPageIndexClient:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.requests: list[dict[str, object]] = []

    async def index_document(
        self,
        *,
        document_id: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.requests.append(
            {"action": "index", "document_id": document_id, "content_length": len(content)}
        )
        if self.should_fail:
            raise RuntimeError("PageIndex unavailable")
        return {"status": "indexed", "document_id": document_id}

    async def search(
        self,
        *,
        document_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, object]]:
        self.requests.append(
            {"action": "search", "document_id": document_id, "query": query, "top_k": top_k}
        )
        if self.should_fail:
            raise RuntimeError("PageIndex unavailable")
        return [
            {
                "chunk_id": f"chunk-{i}",
                "content": f"Relevant content {i} for query: {query}",
                "score": 0.9 - (i * 0.1),
                "chapter": f"Chapter {i + 1}",
                "page": i + 1,
            }
            for i in range(min(top_k, 3))
        ]

    async def ask(
        self,
        *,
        document_id: str,
        question: str,
        context_chunks: int = 3,
    ) -> dict[str, object]:
        self.requests.append(
            {
                "action": "ask",
                "document_id": document_id,
                "question": question,
                "context_chunks": context_chunks,
            }
        )
        if self.should_fail:
            raise RuntimeError("PageIndex unavailable")
        return {
            "answer": f"Answer to: {question}",
            "source_chunks": [
                {"chunk_id": "chunk-0", "content": "Source content 1"},
                {"chunk_id": "chunk-1", "content": "Source content 2"},
            ],
            "confidence": 0.85,
        }

    async def get_study_recommendation(
        self,
        *,
        document_id: str,
        user_id: str,
    ) -> dict[str, object]:
        self.requests.append(
            {"action": "recommend", "document_id": document_id, "user_id": user_id}
        )
        if self.should_fail:
            raise RuntimeError("PageIndex unavailable")
        return {
            "weak_chapters": [
                {
                    "chapter": "Chapter 3",
                    "reason": "Low accuracy in related questions",
                    "next_step": "Review Chapter 3.1-3.3",
                }
            ],
            "suggested_questions": [{"question_id": str(uuid4()), "reason": "Frequently missed"}],
        }


def build_backend(*, should_fail: bool = False) -> tuple[PageIndexBackend, MockPageIndexClient]:
    client = MockPageIndexClient(should_fail=should_fail)
    config = PageIndexConfig(base_url="http://localhost:8080", timeout_seconds=30)
    backend = PageIndexBackend(client=client, config=config)
    return backend, client


class TestPageIndexBackend:
    @pytest.mark.asyncio
    async def test_search_returns_structured_results(self) -> None:
        backend, _client = build_backend()
        doc_id = str(uuid4())

        results = await backend.search(document_id=doc_id, query="test query", top_k=3)

        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.chunk_id for r in results)
        assert all(r.content for r in results)
        assert all(0 <= r.score <= 1 for r in results)

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self) -> None:
        backend, _client = build_backend()
        doc_id = str(uuid4())

        results = await backend.search(document_id=doc_id, query="test", top_k=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_ask_returns_answer_with_sources(self) -> None:
        backend, _client = build_backend()
        doc_id = str(uuid4())

        result = await backend.ask(document_id=doc_id, question="What is this about?")

        assert result.answer is not None
        assert len(result.source_chunks) > 0
        assert result.confidence >= 0

    @pytest.mark.asyncio
    async def test_ask_scoped_to_single_document(self) -> None:
        backend, client = build_backend()
        doc_id = str(uuid4())

        await backend.ask(document_id=doc_id, question="test question")

        request = client.requests[-1]
        assert request["action"] == "ask"
        assert request["document_id"] == doc_id

    @pytest.mark.asyncio
    async def test_get_study_recommendation_returns_weak_chapters(self) -> None:
        backend, _client = build_backend()
        doc_id = str(uuid4())
        user_id = str(uuid4())

        result = await backend.get_study_recommendation(document_id=doc_id, user_id=user_id)

        assert len(result.weak_chapters) >= 0
        for chapter in result.weak_chapters:
            assert chapter.chapter is not None
            assert chapter.reason is not None
            assert chapter.next_step is not None

    @pytest.mark.asyncio
    async def test_index_document_returns_success(self) -> None:
        backend, _client = build_backend()
        doc_id = str(uuid4())

        result = await backend.index_document(document_id=doc_id, content="Sample document content")

        assert result.status == "indexed"
        assert result.document_id == doc_id

    @pytest.mark.asyncio
    async def test_search_handles_failure_gracefully(self) -> None:
        backend, _client = build_backend(should_fail=True)
        doc_id = str(uuid4())

        with pytest.raises(RuntimeError):
            await backend.search(document_id=doc_id, query="test")

    @pytest.mark.asyncio
    async def test_ask_handles_failure_gracefully(self) -> None:
        backend, _client = build_backend(should_fail=True)
        doc_id = str(uuid4())

        with pytest.raises(RuntimeError):
            await backend.ask(document_id=doc_id, question="test")
