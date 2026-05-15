"""Application configuration."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _resolve_env_file() -> Path:
    base_dir = Path(__file__).resolve().parents[2]
    env = os.getenv("APP_ENV", "local").lower()
    env_file = base_dir / f".env.{env}"
    if env_file.exists():
        return env_file
    fallback = base_dir / ".env"
    return fallback if fallback.exists() else env_file


def read_env_file_value(key: str) -> str | None:
    env_file = _resolve_env_file()
    if not env_file.exists():
        return None
    value: str | None = None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, raw_value = stripped.split("=", 1)
        if name.strip() == key:
            value = raw_value.strip().strip('"').strip("'") or None
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
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
    pageindex_url: str = "http://localhost:8080/pageindex"
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
    r2_bucket_name: str | None = None
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_public_url: str | None = None
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
    frontend_base_url: str = "http://localhost:5173"
    creem_api_base_url: str = "https://api.creem.io"
    creem_api_key: str | None = None
    creem_webhook_secret: str | None = None
    creem_product_coin_60: str | None = None
    creem_product_coin_300: str | None = None
    creem_product_coin_680: str | None = None
    creem_product_coin_1500: str | None = None
    creem_product_coin_3500: str | None = None
    creem_product_sub_monthly: str | None = None
    creem_product_sub_quarterly: str | None = None
    creem_product_sub_yearly: str | None = None
    creem_checkout_success_url: str = "http://localhost:5173/settings"
    creem_checkout_cancel_url: str = "http://localhost:5173/pricing"
    premium_regions: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "US", "GB", "CA", "AU", "DE", "FR", "JP", "SG", "NL", "SE", "CH", "NO", "DK", "FI", "IE", "NZ", "BE", "AT", "IT", "ES",
        ]
    )
    developing_regions: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "IN", "ID", "PH", "VN", "TH", "MY", "BR", "MX", "AR", "CO", "PE", "EG", "NG", "KE", "PK", "BD", "UA", "RO", "BG",
        ]
    )

    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_callback_url: str = "http://localhost:8000/api/v1/auth/oauth/github/callback"

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_callback_url: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    microsoft_tenant_id: str = "common"
    microsoft_callback_url: str = "http://localhost:8000/api/v1/auth/oauth/microsoft/callback"

    resend_api_key: str | None = None
    resend_from_email: str = "Xirang <noreply@example.com>"
    resend_timeout_seconds: float = 10.0
    verification_code_secret: str | None = None
    verification_code_ttl_seconds: int = 600
    verification_code_resend_cooldown_seconds: int = 60
    verification_code_max_attempts: int = 5

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

    @field_validator("premium_regions", "developing_regions", mode="before")
    @classmethod
    def parse_region_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return [item.strip().upper() for item in value if isinstance(item, str) and item.strip()]
        if not value:
            return []
        return [item.strip().upper() for item in value.split(",") if item.strip()]

    @property
    def llm_api_key(self) -> str | None:
        if self.openai_api_key:
            return self.openai_api_key
        if self.nvidia_api_key:
            return self.nvidia_api_key
        return None

    @property
    def llm_base_url(self) -> str | None:
        if self.openai_api_key:
            return self.openai_base_url
        if self.nvidia_api_key:
            return self.nvidia_base_url
        return None

    @property
    def llm_model(self) -> str:
        if self.openai_api_key:
            return self.openai_model
        if self.nvidia_api_key:
            return self.nvidia_model
        return self.openai_model

    @property
    def r2_endpoint_url(self) -> str | None:
        if self.r2_account_id:
            return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
