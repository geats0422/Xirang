"""API routes for jobs."""

from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
