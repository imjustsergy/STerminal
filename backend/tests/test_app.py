from fastapi.testclient import TestClient

from app.main import app


def test_app_imports() -> None:
    assert app is not None


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_frontend_origin() -> None:
    """feat-8: el frontend Svelte se sirve en un origen/puerto distinto del backend —
    sin CORS, el navegador bloquearía `fetch` a `POST /command`."""
    client = TestClient(app)
    response = client.get(
        "/health", headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
