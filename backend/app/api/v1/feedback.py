"""Feedback API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.services.review.facade import ReviewService
from app.services.review.service import create_review_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


# This function is the dependency that can be overridden in tests
async def get_review_service(session: AsyncSession = Depends(get_db_session)) -> ReviewService:
    return create_review_service(session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: dict[str, str | None],
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> dict[str, str | None]:
    """Submit feedback."""
    from app.services.review.schemas import FeedbackCreate

    feedback = FeedbackCreate(
        question_id=UUID(request["question_id"]),
        document_id=UUID(request["document_id"]),
        run_id=UUID(rid) if (rid := request["run_id"]) else None,
        feedback_type=request["feedback_type"] or "",
        detail_text=request.get("detail_text"),
    )
    result = await service.submit_feedback(user_id=user_id, feedback=feedback)
    return {
        "id": str(result.id),
        "feedback_type": result.feedback_type,
        "detail_text": result.detail_text,
        "status": result.status,
    }


@router.get("/{feedback_id}")
async def get_feedback(
    feedback_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> dict[str, str | None]:
    """Get feedback by ID."""
    result = await service.get_feedback(feedback_id)
    if not result or result.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return {
        "id": str(result.id),
        "feedback_type": result.feedback_type,
        "detail_text": result.detail_text,
        "status": result.status,
    }


@router.get("")
async def list_feedback(
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> dict[str, list[dict[str, str]] | int]:
    """List user feedback."""
    results = await service.list_user_feedback(user_id)
    items = [{"id": str(r.id), "feedback_type": r.feedback_type} for r in results]
    return {"items": items, "total": len(items)}


@router.post("/summarize")
async def summarize_feedback(
    request: dict[str, list[str]],
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> dict[str, Any]:
    """Summarize feedback."""
    feedback_ids = [UUID(fid) for fid in request.get("feedback_ids", [])]
    result = await service.summarize_feedback(feedback_ids)
    return dict(result)
