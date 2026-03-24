"""Runs API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.models.runs import RunMode
from app.db.session import get_db_session
from app.repositories.run_repository import RunRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.runs.service import RunService
from app.services.wallet.service import WalletService

router = APIRouter(prefix="/runs", tags=["runs"])


async def get_run_service(session: AsyncSession = Depends(get_db_session)) -> RunService:
    wallet_service = WalletService(repository=WalletRepository(session))
    return RunService(repository=RunRepository(session), wallet_service=wallet_service)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(
    request: dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
) -> dict[str, Any]:
    """Create a new run."""
    question_count = request.get("question_count", 5)
    if not isinstance(question_count, int) or question_count < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="question_count"
        )

    mode = request.get("mode", RunMode.ENDLESS.value)
    run_mode = RunMode(mode)

    result, questions = await service.create_run(
        user_id=user_id,
        document_id=UUID(request.get("document_id")),
        mode=run_mode,
        question_count=question_count,
    )
    return {
        "run_id": str(result.id),
        "mode": str(result.mode),
        "status": result.status,
        "questions": [
            {
                "id": str(q.id),
                "text": q.question_text,
                "options": [{"id": str(o["id"]), "text": o["text"]} for o in q.options],
            }
            for q in questions
        ],
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
        },
    }


@router.get("/{run_id}/settlement")
async def get_settlement(
    run_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_run_service),
) -> dict[str, Any]:
    """Get run settlement."""
    settlement = await service.get_settlement(run_id)
    return {
        "run_id": str(settlement.run_id),
        "xp_earned": settlement.xp_earned,
        "coins_earned": settlement.coins_earned,
        "combo_max": settlement.combo_max,
        "accuracy": settlement.accuracy,
        "correct_count": settlement.correct_count,
        "total_questions": settlement.total_count,
        "correct_answers": settlement.correct_count,
    }
