"""System routes."""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_session_factory

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "api_version": "v1",
    }


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def health_ready() -> dict[str, str]:
    settings = get_settings()
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": settings.app_name,
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": settings.app_name,
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
