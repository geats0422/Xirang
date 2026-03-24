from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user_id
from app.schemas.review import (
    ExplainMistakeRequest,
    ExplainMistakeResponse,
    MistakeListResponse,
    MistakeResponse,
    RuleCandidateListResponse,
    RuleCandidateResponse,
)
from app.services.review.facade import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


async def get_review_service() -> ReviewService:
    raise NotImplementedError("ReviewService dependency must be overridden")


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mistake not found")
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
async def list_user_mistakes(
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> MistakeListResponse:
    mistakes = await service.list_mistakes_by_user(user_id)
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
    user_id: UUID = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service),
) -> ExplainMistakeResponse:
    try:
        explanation = await service.explain_mistake(
            mistake_id=mistake_id,
            question_text=request.question_text,
            document_context=request.document_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return ExplainMistakeResponse(mistake_id=mistake_id, explanation=explanation)


@router.get("/rules", response_model=RuleCandidateListResponse)
async def list_rule_candidates(
    status_filter: str | None = None,
    service: ReviewService = Depends(get_review_service),
) -> RuleCandidateListResponse:
    rules = await service.list_rule_candidates(status=status_filter)
    return RuleCandidateListResponse(
        items=[
            RuleCandidateResponse(
                id=UUID(r["id"]),
                rule_type=r["rule_type"],
                title=r["title"],
                content=r["content"],
                status=r["status"],
                source_job_id=UUID(r["source_job_id"]),
            )
            for r in rules
        ],
        total=len(rules),
    )
