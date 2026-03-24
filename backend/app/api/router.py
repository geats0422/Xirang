"""Application router registration."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.document_ai import router as document_ai_router
from app.api.v1.documents import router as documents_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.leaderboard import router as leaderboard_router
from app.api.v1.profile import router as profile_router
from app.api.v1.review import router as review_router
from app.api.v1.runs import router as runs_router
from app.api.v1.settings import router as settings_router
from app.api.v1.shop import router as shop_router
from app.api.v1.system import router as system_router


def build_api_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(auth_router)
    api_router.include_router(documents_router)
    api_router.include_router(document_ai_router)
    api_router.include_router(feedback_router)
    api_router.include_router(jobs_router)
    api_router.include_router(leaderboard_router)
    api_router.include_router(profile_router)
    api_router.include_router(review_router)
    api_router.include_router(runs_router)
    api_router.include_router(settings_router)
    api_router.include_router(shop_router)
    api_router.include_router(system_router)
    return api_router


api_router = build_api_router()
