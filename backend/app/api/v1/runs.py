"""Runs API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.models.documents import DocumentStatus
from app.db.models.runs import RunMode
from app.db.session import get_db_session
from app.repositories.document_repository import DocumentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.runs.exceptions import InvalidRunStateError, RunNotFoundError
from app.services.runs.service import RunService
from app.services.wallet.service import InsufficientBalanceError, WalletService

router = APIRouter(prefix="/runs", tags=["runs"])


async def get_run_service(session: AsyncSession = Depends(get_db_session)) -> RunService:
    wallet_service = WalletService(repository=WalletRepository(session))
    return RunService(repository=RunRepository(session), wallet_service=wallet_service)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(
    request: dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Create a new run."""
    question_count = request.get("question_count", 5)
    if not isinstance(question_count, int) or question_count < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="question_count"
        )

    mode = request.get("mode", RunMode.ENDLESS.value)
    run_mode = RunMode(mode)

    document_id = request.get("document_id")
    if not isinstance(document_id, str):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="document_id")

    document_repo = DocumentRepository(session)
    document = await document_repo.get_document_by_id(UUID(document_id))
    if document is None or document.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")
    if document.ingest_status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="document_not_ready",
        )

    result, questions = await service.create_run(
        user_id=user_id,
        document_id=UUID(document_id),
        mode=run_mode,
        question_count=question_count,
        path_id=request.get("path_id"),
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
            }
            for q in questions
        ],
    }


@router.get("/path-options")
async def list_path_options(
    mode: str,
    document_id: str,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    document_repo = DocumentRepository(session)
    document = await document_repo.get_document_by_id(UUID(document_id))
    if document is None or document.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")
    if document.ingest_status != DocumentStatus.READY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="document_not_ready")

    run_mode = RunMode(mode)
    options = await service.list_path_options(
        mode=run_mode,
        document_id=UUID(document_id),
        user_id=user_id,
    )
    return {
        "mode": run_mode.value,
        "options": options,
    }


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
        text_answer=request.get("text_answer"),  # For FILL_IN_BLANK questions
    )

    # Get question details for feedback (correct answer, explanation)
    question_info = await service.get_question_info(
        run_id=run_id,
        question_id=UUID(request.get("question_id")),
    )

    # Build feedback data
    feedback = {
        "correct_answer": question_info.get("correct_answer") if question_info else None,
        "correct_option_ids": question_info.get("correct_option_ids", []) if question_info else [],
        "explanation": question_info.get("explanation") if question_info else None,
    }

    return {
        "is_correct": result.is_correct,
        "answer": {
            "id": str(result.answer.id),
            "question_id": str(result.answer.question_id),
            "selected_option_ids": [str(v) for v in result.answer.selected_option_ids],
            "is_correct": result.answer.is_correct,
        },
        "feedback": feedback,  # Include correct answer and explanation for learning
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


@router.post("/{run_id}/revive")
async def use_revive(
    run_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
) -> dict[str, Any]:
    try:
        refreshed_run, balance = await service.use_revive(run_id=run_id, owner_user_id=user_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    except InvalidRunStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {
        "run": {
            "id": str(refreshed_run.id),
            "status": str(refreshed_run.status),
            "score": refreshed_run.score,
            "state": refreshed_run.mode_state,
        },
        "coin_balance": balance,
        "revive_cost": service.REVIVE_COIN_COST,
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
