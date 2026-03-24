"""System routes."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return API health status."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "api_version": "v1",
    }


@router.get("/version")
def version() -> dict[str, str]:
    """Return service version metadata."""
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
