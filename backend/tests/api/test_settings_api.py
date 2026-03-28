from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings
from app.main import create_app


def create_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: uuid4()
    return TestClient(app)


def test_ai_config_endpoint_returns_openai_compatible_config_from_nvidia_env(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b")

    get_settings.cache_clear()
    client = create_test_client()

    response = client.get("/api/v1/settings/ai-config")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "openai-compatible",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/nemotron-3-nano-30b-a3b",
        "configured": True,
    }


def test_ai_config_endpoint_accepts_legacy_nividia_env_keys(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_BASE_URL", raising=False)
    monkeypatch.setenv("NIVIDIA_BUILD_API_KEY", "legacy-nvapi-key")
    monkeypatch.setenv("NIVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    get_settings.cache_clear()
    client = create_test_client()

    response = client.get("/api/v1/settings/ai-config")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai-compatible"
    assert body["base_url"] == "https://integrate.api.nvidia.com/v1"
    assert body["configured"] is True
