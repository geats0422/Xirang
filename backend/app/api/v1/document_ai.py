"""Document AI API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

router = APIRouter(prefix="", tags=["document-ai"])


async def get_ask_service() -> Any:
    raise NotImplementedError("AskService dependency must be overridden")


async def get_recommendation_service() -> Any:
    raise NotImplementedError("RecommendationService dependency must be overridden")


@router.post("/documents/{document_id}/ask")
async def ask_document(
    document_id: UUID,
    request: dict[str, Any],
    service: Any = Depends(get_ask_service),
) -> dict[str, Any]:
    """Ask a question about a document."""
    result = await service.ask(
        question=request.get("question", ""),
        document_id=document_id,
        context_chunks=request.get("context_chunks", 5),
    )
    return {
        "answer": result.answer,
        "source_chunks": result.source_chunks,
        "confidence": result.confidence,
    }


@router.get("/documents/{document_id}/study-recommendation")
async def get_study_recommendation(
    document_id: UUID,
    user_id: UUID,
    service: Any = Depends(get_recommendation_service),
) -> dict[str, Any]:
    result = await service.get_recommendation(user_id=user_id, document_id=document_id)
    return {
        "weak_chapters": [
            {
                "chapter": r.chapter,
                "reason": r.reason,
                "next_step": r.next_step,
            }
            for r in (result.weak_chapters or [])
        ],
        "suggested_questions": [
            {"question_id": q.question_id, "reason": q.reason}
            for q in (result.suggested_questions or [])
        ],
    }
