from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.notification_repository import NotificationRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.quest import QuestClaimResponse, QuestListResponse
from app.services.notification.service import NotificationService
from app.services.quest.service import (
    QuestAlreadyClaimedError,
    QuestExpiredError,
    QuestNotCompletedError,
    QuestNotFoundError,
    QuestService,
)

router = APIRouter(prefix="/quests", tags=["quests"])


async def get_quest_repository(session: AsyncSession = Depends(get_db_session)) -> QuestRepository:
    return QuestRepository(session)


async def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return NotificationRepository(session)


async def get_wallet_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WalletRepository:
    return WalletRepository(session)


def get_quest_service(
    quest_repo: QuestRepository = Depends(get_quest_repository),
    wallet_repo: WalletRepository = Depends(get_wallet_repository),
    notification_repo: NotificationRepository = Depends(get_notification_repository),
) -> QuestService:
    return QuestService(
        quest_repository=quest_repo,
        wallet_repository=wallet_repo,
        notification_service=NotificationService(notification_repo),
    )


@router.get("", response_model=QuestListResponse)
async def get_quests(
    user_id: UUID = Depends(get_current_user_id),
    service: QuestService = Depends(get_quest_service),
) -> QuestListResponse:
    return await service.get_user_quests(user_id)


@router.post("/{assignment_id}/claim", response_model=QuestClaimResponse)
async def claim_quest_reward(
    assignment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: QuestService = Depends(get_quest_service),
) -> QuestClaimResponse:
    try:
        return await service.claim_reward(user_id, assignment_id)
    except QuestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except QuestNotCompletedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except QuestAlreadyClaimedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except QuestExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e)) from e
