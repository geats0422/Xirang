"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.integrations.pageindex.runtime import ensure_pageindex_ready_with_launch


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    pageindex_ready, managed_process = await ensure_pageindex_ready_with_launch(settings)
    if not pageindex_ready:
        raise RuntimeError(f"PageIndex did not become ready at {settings.pageindex_url}")

    app.state.pageindex_process = managed_process

    try:
        yield
    finally:
        if managed_process is not None and managed_process.poll() is None:
            managed_process.terminate()
            try:
                managed_process.wait(timeout=5)
            except Exception:
                managed_process.kill()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
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
    return app


app = create_app()
