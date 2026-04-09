"""Learning paths API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings
from app.db.session import get_db_session
from app.integrations.agents.client import AgentsClient
from app.repositories.learning_path_repository import LearningPathRepository
from app.schemas.learning_path import GenerateLearningPathRequest, LearningPathResponse
from app.services.learning_path.service import LearningPathService

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


def get_learning_path_service(
    session: AsyncSession = Depends(get_db_session),
) -> LearningPathService:
    repo = LearningPathRepository(session)
    settings = get_settings()
    llm_client = None
    if settings.llm_api_key:
        llm_client = AgentsClient()
    return LearningPathService(repo, llm_client=llm_client)


@router.get("", response_model=LearningPathResponse)
async def get_learning_path(
    document_id: UUID,
    mode: str,
    service: LearningPathService = Depends(get_learning_path_service),
    user_id: UUID = Depends(get_current_user_id),
) -> LearningPathResponse:
    """Get learning path for a document."""
    result = await service.get_learning_path(document_id, user_id, mode)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    return result


@router.post("/generate", status_code=status.HTTP_201_CREATED, response_model=LearningPathResponse)
async def generate_learning_path(
    request: GenerateLearningPathRequest,
    service: LearningPathService = Depends(get_learning_path_service),
    user_id: UUID = Depends(get_current_user_id),
) -> LearningPathResponse:
    try:
        result = await service.generate_learning_path(request, user_id)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
