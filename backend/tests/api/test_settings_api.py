from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings
from app.main import create_app


def create_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: uuid4()
    return TestClient(app)


def test_ai_config_endpoint_returns_openai_compatible_config(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "nvapi-test-key")
    monkeypatch.setenv("BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("MODEL_NAME", "nvidia/nemotron-3-nano-30b-a3b")

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


def test_ai_config_endpoint_marks_unconfigured_when_api_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("BASE_URL", "https://integrate.api.nvidia.com/v1")

    get_settings.cache_clear()
    client = create_test_client()

    response = client.get("/api/v1/settings/ai-config")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai-compatible"
    assert body["base_url"] == "https://integrate.api.nvidia.com/v1"
    assert body["configured"] is False


def test_ai_models_endpoint_returns_available_models(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_NAME", "nvidia/test-model")
    get_settings.cache_clear()
    client = create_test_client()

    response = client.get("/api/v1/settings/ai-models")

    assert response.status_code == 200
    assert response.json() == {"available_models": ["nvidia/test-model"]}
