"""Runs API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.models.documents import DocumentStatus, QuestionSetStatus
from app.db.models.runs import RunMode
from app.db.session import get_db_session
from app.repositories.document_repository import DocumentRepository
from app.repositories.learning_path_repository import LearningPathRepository
from app.repositories.run_repository import RunRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.learning_paths.service import (
    LearningPathService,
    PathGenerationFailedError,
    PathGenerationInProgressError,
    RegenerationLimitExceededError,
)
from app.services.runs.service import RunService
from app.services.wallet.service import WalletService

router = APIRouter(prefix="/runs", tags=["runs"])


async def get_run_service(session: AsyncSession = Depends(get_db_session)) -> RunService:
    wallet_service = WalletService(repository=WalletRepository(session))
    return RunService(repository=RunRepository(session), wallet_service=wallet_service)


async def get_learning_path_service(
    session: AsyncSession = Depends(get_db_session),
) -> LearningPathService:
    return LearningPathService(repository=LearningPathRepository(session))


async def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRepository:
    return DocumentRepository(session)


async def ensure_document_ready_for_run(
    *,
    document_id: UUID,
    user_id: UUID,
    repository: DocumentRepository,
) -> None:
    document = await repository.get_document_by_id(document_id)
    if document is None or document.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")

    if document.ingest_status != DocumentStatus.READY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="document_not_ready")

    question_set = await repository.get_question_set_for_document(document_id)
    if (
        question_set is None
        or question_set.status != QuestionSetStatus.READY
        or question_set.question_count < 1
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="question_set_not_ready")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(
    request: dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> dict[str, Any]:
    """Create a new run."""
    question_count = request.get("question_count", 5)
    if not isinstance(question_count, int) or question_count < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="question_count"
        )

    mode = request.get("mode", RunMode.ENDLESS.value)
    try:
        run_mode = RunMode(str(mode))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="mode"
        ) from exc

    document_id_raw = request.get("document_id")
    if not isinstance(document_id_raw, str):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="document_id")
    try:
        document_id = UUID(document_id_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="document_id"
        ) from exc

    path_version_id_raw = request.get("path_version_id")
    level_node_id_raw = request.get("level_node_id")
    try:
        path_version_id = (
            UUID(path_version_id_raw) if isinstance(path_version_id_raw, str) else None
        )
        level_node_id = UUID(level_node_id_raw) if isinstance(level_node_id_raw, str) else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="path_version_id/level_node_id",
        ) from exc

    await ensure_document_ready_for_run(
        document_id=document_id,
        user_id=user_id,
        repository=document_repository,
    )

    result, questions = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=run_mode,
        question_count=question_count,
        path_id=request.get("path_id"),
        path_version_id=path_version_id,
        level_node_id=level_node_id,
        is_legend_review=bool(request.get("is_legend_review", False)),
    )
    return {
        "run_id": str(result.id),
        "mode": str(result.mode),
        "status": result.status,
        "run_state": result.mode_state,
        "questions": [
            {
                "id": str(q.id),
                "text": q.question_text,
                "options": [{"id": str(o["id"]), "text": o["text"]} for o in q.options],
                "source_locator": q.source_locator,
                "supporting_excerpt": q.supporting_excerpt,
            }
            for q in questions
        ],
    }


@router.get("/path-options")
async def list_path_options(
    mode: str,
    document_id: str,
    user_id: UUID = Depends(get_current_user_id),
    service: LearningPathService = Depends(get_learning_path_service),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> Any:
    try:
        document_uuid = UUID(document_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="document_id"
        ) from exc

    await ensure_document_ready_for_run(
        document_id=document_uuid,
        user_id=user_id,
        repository=document_repository,
    )

    try:
        payload = await service.get_path_options(document_id=document_uuid, mode=mode)
    except PathGenerationFailedError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if payload.get("generation_status") == "generating":
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=payload)
    return payload


@router.post("/path-regenerations")
async def trigger_path_regeneration(
    request: dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
    service: LearningPathService = Depends(get_learning_path_service),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> JSONResponse:
    document_id_raw = request.get("document_id")
    mode = request.get("mode")
    if not isinstance(document_id_raw, str) or not isinstance(mode, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="document_id/mode"
        )

    try:
        document_id = UUID(document_id_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="document_id"
        ) from exc

    await ensure_document_ready_for_run(
        document_id=document_id,
        user_id=user_id,
        repository=document_repository,
    )

    try:
        payload = await service.regenerate_path(document_id=document_id, mode=mode, user_id=user_id)
    except RegenerationLimitExceededError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except PathGenerationInProgressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=payload)


@router.get("")
async def list_runs(
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
) -> list[dict[str, Any]]:
    runs = await service.list_runs(user_id)
    return [
        {
            "id": str(r.id),
            "status": str(r.status),
            "mode": str(r.mode),
            "run_state": r.mode_state,
            "started_at": r.started_at.isoformat(),
            "ended_at": None if r.ended_at is None else r.ended_at.isoformat(),
            "score": r.score,
        }
        for r in runs
    ]


@router.post("/{run_id}/answers")
async def submit_answer(
    run_id: UUID,
    request: dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
) -> dict[str, Any]:
    """Submit an answer."""
    result = await service.submit_answer(
        run_id=run_id,
        question_id=UUID(request.get("question_id")),
        selected_option_ids=[UUID(oid) for oid in request.get("selected_option_ids", [])],
        answer_time_ms=request.get("answer_time_ms"),
        owner_user_id=user_id,
    )
    return {
        "is_correct": result.is_correct,
        "answer": {
            "id": str(result.answer.id),
            "question_id": str(result.answer.question_id),
            "selected_option_ids": [str(v) for v in result.answer.selected_option_ids],
            "is_correct": result.answer.is_correct,
        },
        "run": {
            "id": str(result.run.id),
            "status": str(result.run.status),
            "score": result.run.score,
            "state": result.run.mode_state,
        },
        "settlement": None
        if result.settlement is None
        else {
            "run_id": str(result.settlement.run_id),
            "xp_earned": result.settlement.xp_earned,
            "coins_earned": result.settlement.coins_earned,
            "combo_max": result.settlement.combo_max,
            "accuracy": result.settlement.accuracy,
            "correct_count": result.settlement.correct_count,
            "total_count": result.settlement.total_count,
            "path_id": result.run.mode_state.get("path_id"),
            "goal_current": result.run.mode_state.get("goal_current", 0),
            "goal_total": result.run.mode_state.get("goal_total"),
        },
    }


@router.get("/{run_id}/settlement")
async def get_settlement(
    run_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
) -> dict[str, Any]:
    """Get run settlement."""
    run = await service.get_run(run_id, owner_user_id=user_id)
    settlement = await service.get_settlement(run.id)
    return {
        "run_id": str(settlement.run_id),
        "xp_earned": settlement.xp_earned,
        "coins_earned": settlement.coins_earned,
        "combo_max": settlement.combo_max,
        "accuracy": settlement.accuracy,
        "correct_count": settlement.correct_count,
        "total_questions": settlement.total_count,
        "correct_answers": settlement.correct_count,
        "path_id": run.mode_state.get("path_id"),
        "goal_current": run.mode_state.get("goal_current", 0),
        "goal_total": run.mode_state.get("goal_total"),
    }
