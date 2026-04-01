"""FastAPI application entrypoint."""

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "status": "ok",
            "health": "/health",
            "docs": "/docs",
            "api": "/api/v1",
        }

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/health")
    def root_health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
        }

    app.include_router(api_router, prefix="/api/v1")

    from app.integrations.pageindex.mock_server import app as pageindex_app

    app.mount("/pageindex", pageindex_app)

    return app


app = create_app()
