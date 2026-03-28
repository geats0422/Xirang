"""System routes."""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.integrations.pageindex.client import PageIndexClient

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
    pageindex_client = PageIndexClient(
        base_url=settings.pageindex_url,
        timeout_seconds=settings.pageindex_timeout_seconds,
    )

    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        pageindex_ready = await pageindex_client.health_check()
        if not pageindex_ready:
            return {
                "status": "not_ready",
                "service": settings.app_name,
                "database": "connected",
                "pageindex": "disconnected",
            }
        return {
            "status": "ready",
            "service": settings.app_name,
            "database": "connected",
            "pageindex": "connected",
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": settings.app_name,
            "database": "disconnected",
            "pageindex": "unknown",
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
