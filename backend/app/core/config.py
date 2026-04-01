"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


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
    pageindex_url: str = "http://localhost:8000/pageindex"
    pageindex_auto_start: bool = True
    pageindex_timeout_seconds: int = 30
    pageindex_startup_timeout_seconds: int = 30
    pageindex_startup_poll_interval_seconds: float = 1.0
    pageindex_subprocess_log_level: str = "warning"
    pageindex_launch_command: str | None = None
    pageindex_launch_workdir: str | None = None
    pageindex_launch_shell: bool = True
    pageindex_mock_fallback: bool = True
    mineru_url: str = "http://127.0.0.1:8300"
    mineru_timeout_seconds: float = 1800.0
    mineru_backend: str = "hybrid-auto-engine"
    mineru_lang_list: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["ch"])

    # LLM provider configuration (OpenAI-compatible)
    # IMPORTANT: API credentials MUST NOT be modified - these are provided by the project
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    # NVIDIA Build API (primary LLM provider - DO NOT MODIFY)
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
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

    @field_validator("mineru_lang_list", mode="before")
    @classmethod
    def parse_mineru_lang_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not value:
            return ["ch"]
        langs = [item.strip() for item in value.split(",") if item.strip()]
        return langs or ["ch"]

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
    return Settings()
