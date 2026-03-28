"""Application configuration."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Load .env file into os.environ so pydantic_settings can read it
load_dotenv(ENV_FILE, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "xirang-backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    secret_key: str = "local-dev-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/xirang"
    database_echo: bool = False
    pageindex_url: str = "http://localhost:8080"
    pageindex_auto_start: bool = True
    pageindex_timeout_seconds: int = 30
    pageindex_startup_timeout_seconds: int = 30
    pageindex_startup_poll_interval_seconds: float = 1.0
    pageindex_subprocess_log_level: str = "warning"
    pageindex_launch_command: str | None = None
    pageindex_launch_workdir: str | None = None
    pageindex_launch_shell: bool = True
    pageindex_mock_fallback: bool = True

    # LLM provider configuration (OpenAI-compatible)
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    nvidia_base_url: str | None = None
    nvidia_api_key: str | None = None
    nvidia_model: str = "nvidia/nemotron-3-nano-30b-a3b"

    storage_mode: str = "local"
    upload_dir: str = ".data/uploads"
    max_file_size_bytes: int = 50 * 1024 * 1024
    allowed_extensions: list[str] = Field(
        default_factory=lambda: ["pdf", "doc", "docx", "ppt", "pptx", "txt", "md"]
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
        ],
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @property
    def llm_api_key(self) -> str | None:
        if self.openai_api_key:
            return self.openai_api_key
        if self.nvidia_api_key:
            return self.nvidia_api_key
        return None

    @property
    def llm_base_url(self) -> str | None:
        if self.openai_base_url:
            return self.openai_base_url
        if self.nvidia_base_url:
            return self.nvidia_base_url
        return None

    @property
    def llm_model(self) -> str:
        if self.openai_api_key:
            return self.openai_model
        if self.nvidia_api_key:
            return self.nvidia_model
        return self.openai_model


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    # Backward compatibility: tolerate old misspelled NIVIDIA_* keys in existing .env
    if settings.nvidia_base_url is None:
        legacy_base = os.getenv("NIVIDIA_BASE_URL")
        if isinstance(legacy_base, str) and legacy_base.strip():
            settings.nvidia_base_url = legacy_base.strip()

    if settings.nvidia_api_key is None:
        legacy_key = os.getenv("NIVIDIA_BUILD_API_KEY") or os.getenv("NIVIDIA_API_KEY")
        if isinstance(legacy_key, str) and legacy_key.strip():
            settings.nvidia_api_key = legacy_key.strip()

    return settings
