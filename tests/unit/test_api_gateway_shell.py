from fastapi.testclient import TestClient

from gnxthire_api_gateway.main import create_app


def test_health_endpoint_is_non_business_shell() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_declares_phase0_state() -> None:
    client = TestClient(create_app())

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["phase"] == "0"
