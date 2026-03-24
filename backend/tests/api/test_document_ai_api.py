from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.documents.ask_service import AskResponse, AskService
from app.services.documents.recommendation_service import (
    ChapterRecommendation,
    QuestionSuggestion,
    RecommendationResponse,
    RecommendationService,
)


@pytest.fixture
def mock_ask_service() -> AsyncMock:
    service = AsyncMock(spec=AskService)
    service.ask.return_value = AskResponse(
        answer="This is a test answer",
        source_chunks=[
            {"chunk_id": "chunk-1", "content": "Source content 1"},
        ],
        confidence=0.85,
    )
    return service


@pytest.fixture
def mock_recommendation_service() -> AsyncMock:
    service = AsyncMock(spec=RecommendationService)
    service.get_recommendation.return_value = RecommendationResponse(
        weak_chapters=[
            ChapterRecommendation(
                chapter="Chapter 3",
                reason="Low accuracy in related questions",
                next_step="Review Chapter 3.1-3.3",
            )
        ],
        suggested_questions=[
            QuestionSuggestion(
                question_id=str(uuid4()),
                reason="Frequently missed",
            )
        ],
    )
    return service


class TestDocumentAIAPI:
    @pytest.mark.asyncio
    async def test_ask_endpoint_returns_answer(
        self,
        mock_ask_service: AsyncMock,
    ) -> None:
        from app.api.v1.document_ai import get_ask_service

        app.dependency_overrides[get_ask_service] = lambda: mock_ask_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            doc_id = uuid4()
            response = await client.post(
                f"/api/v1/documents/{doc_id}/ask",
                json={"question": "What is this about?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "This is a test answer"
        assert "source_chunks" in data
        assert "confidence" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_ask_endpoint_respects_context_chunks(
        self,
        mock_ask_service: AsyncMock,
    ) -> None:
        from app.api.v1.document_ai import get_ask_service

        app.dependency_overrides[get_ask_service] = lambda: mock_ask_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            doc_id = uuid4()
            response = await client.post(
                f"/api/v1/documents/{doc_id}/ask",
                json={"question": "What is this about?", "context_chunks": 5},
            )

        assert response.status_code == 200
        mock_ask_service.ask.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_study_recommendation_endpoint_returns_recommendations(
        self,
        mock_recommendation_service: AsyncMock,
    ) -> None:
        from app.api.v1.document_ai import get_recommendation_service

        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            doc_id = uuid4()
            user_id = uuid4()
            response = await client.get(
                f"/api/v1/documents/{doc_id}/study-recommendation",
                params={"user_id": str(user_id)},
            )

        assert response.status_code == 200
        data = response.json()
        assert "weak_chapters" in data
        assert "suggested_questions" in data
        assert len(data["weak_chapters"]) == 1
        assert data["weak_chapters"][0]["chapter"] == "Chapter 3"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_study_recommendation_requires_user_id(
        self,
        mock_recommendation_service: AsyncMock,
    ) -> None:
        from app.api.v1.document_ai import get_recommendation_service

        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            doc_id = uuid4()
            response = await client.get(
                f"/api/v1/documents/{doc_id}/study-recommendation",
            )

        assert response.status_code == 422

        app.dependency_overrides.clear()
