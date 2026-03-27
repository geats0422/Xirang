"""System route tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def create_test_client() -> TestClient:
    return TestClient(create_app())


def test_root_health_returns_ok_payload() -> None:
    client = create_test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "xirang-backend",
    }


def test_api_v1_health_returns_ok_payload() -> None:
    client = create_test_client()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "xirang-backend",
        "api_version": "v1",
    }


def test_api_v1_version_returns_build_metadata() -> None:
    client = create_test_client()

    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json() == {
        "service": "xirang-backend",
        "version": "0.1.0",
        "environment": "development",
    }


def test_root_live_returns_alive_payload() -> None:
    client = create_test_client()

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_root_ready_endpoint_is_reachable() -> None:
    client = create_test_client()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "not_ready"}
    assert payload["service"] == "xirang-backend"
