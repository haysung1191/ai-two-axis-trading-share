from fastapi.testclient import TestClient

from app.main import create_app


def test_status_endpoint_returns_service_health() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "autonomous-trading-platform"
    assert body["version"] == "0.1.0"

