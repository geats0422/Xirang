from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.notification_repository import NotificationRepository
from app.services.notification.schemas import NotificationListResponse, NotificationResponse
from app.services.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return NotificationRepository(session)


def get_notification_service(
    repo: NotificationRepository = Depends(get_notification_repository),
) -> NotificationService:
    return NotificationService(repo)


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    return await service.get_user_notifications(user_id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse | None)
async def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse | None:
    return await service.mark_read(notification_id)


@router.post("/read-all")
async def mark_all_notifications_read(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    updated_count = await service.mark_all_read(user_id)
    return {"updated_count": updated_count}
