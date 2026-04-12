from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.schemas.review import (
    ExplainMistakeRequest,
    ExplainMistakeResponse,
    MistakeListResponse,
    MistakeResponse,
    RuleCandidateListResponse,
    RuleCandidateResponse,
)
from app.services.review.facade import ReviewService
from app.services.review.service import create_review_service

router = APIRouter(prefix="/review", tags=["review"])


async def get_review_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReviewService:
    return create_review_service(session)


@router.post("/mistakes", response_model=MistakeResponse, status_code=status.HTTP_201_CREATED)
async def create_mistake(
    question_id: UUID,
    document_id: UUID,
    run_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> MistakeResponse:
    mistake = await service.create_mistake(
        user_id=user_id,
        question_id=question_id,
        document_id=document_id,
        run_id=run_id,
    )
    return MistakeResponse(
        id=mistake.id,
        user_id=mistake.user_id,
        question_id=mistake.question_id,
        document_id=mistake.document_id,
        run_id=mistake.run_id,
        explanation=mistake.explanation,
        created_at=mistake.created_at,
    )


@router.get("/mistakes/{mistake_id}", response_model=MistakeResponse)
async def get_mistake(
    mistake_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> MistakeResponse:
    mistake = await service.get_mistake(mistake_id)
    if not mistake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mistake not found",
        )
    if mistake.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this mistake",
        )
    return MistakeResponse(
        id=mistake.id,
        user_id=mistake.user_id,
        question_id=mistake.question_id,
        document_id=mistake.document_id,
        run_id=mistake.run_id,
        explanation=mistake.explanation,
        created_at=mistake.created_at,
    )


@router.get("/mistakes", response_model=MistakeListResponse)
async def list_mistakes(
    limit: int = 50,
    offset: int = 0,
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> MistakeListResponse:
    mistakes = await service.list_mistakes_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return MistakeListResponse(
        items=[
            MistakeResponse(
                id=m.id,
                user_id=m.user_id,
                question_id=m.question_id,
                document_id=m.document_id,
                run_id=m.run_id,
                explanation=m.explanation,
                created_at=m.created_at,
            )
            for m in mistakes
        ],
        total=len(mistakes),
    )


@router.post("/mistakes/{mistake_id}/explain", response_model=ExplainMistakeResponse)
async def explain_mistake(
    mistake_id: UUID,
    request: ExplainMistakeRequest,
    service: ReviewService = Depends(get_review_service),
) -> ExplainMistakeResponse:
    explanation = await service.explain_mistake(
        mistake_id=mistake_id,
        question_text=request.question_text,
        document_context=request.document_context,
    )
    return ExplainMistakeResponse(mistake_id=mistake_id, explanation=explanation)


@router.get("/rules/candidates", response_model=RuleCandidateListResponse)
async def list_rule_candidates(
    status: str | None = None,
    limit: int = 50,
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> RuleCandidateListResponse:
    candidates = await service.list_rule_candidates(
        status=status,
        limit=limit,
    )
    return RuleCandidateListResponse(
        items=[
            RuleCandidateResponse(
                id=c["id"],
                source_job_id=c["source_job_id"],
                rule_type=c["rule_type"],
                title=c["title"],
                content=c["content"],
                status=c["status"],
                created_at=c["created_at"],
            )
            for c in candidates
        ],
        total=len(candidates),
    )
