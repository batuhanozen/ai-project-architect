import json
import logging
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from architect.main import app, create_app

client = TestClient(app)


def test_liveness_does_not_require_database() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_readiness_succeeds_when_database_responds() -> None:
    with patch("architect.api.health.get_engine") as get_engine:
        connection = MagicMock()
        get_engine.return_value.connect.return_value.__enter__.return_value = connection
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    connection.execute.assert_called_once()


def test_readiness_returns_safe_error_when_database_fails() -> None:
    with patch("architect.api.health.get_engine") as get_engine:
        get_engine.return_value.connect.side_effect = OperationalError("SELECT 1", {}, Exception())
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_cors_restricts_unknown_origin() -> None:
    response = client.get("/health/live", headers={"Origin": "https://not-allowed.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_configured_origin_and_exposes_request_id() -> None:
    response = client.get("/health/live", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-expose-headers"] == "X-Request-ID"
    preflight = client.options(
        "/health/live",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 400


def test_request_logs_do_not_include_query_strings_or_unknown_paths(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="architect.main"):
        response = client.get("/private_value?token=private_token")
    messages = [record.message for record in caplog.records if record.name == "architect.main"]
    assert "private_value" not in "".join(messages)
    assert "private_token" not in "".join(messages)
    record = json.loads(messages[-1])
    assert record["route"] == "<unmatched>"
    assert record["status"] == 404
    assert str(UUID(record["request_id"])) == response.headers["X-Request-ID"]


def test_unexpected_error_is_safe_and_has_a_request_id(caplog) -> None:
    test_app = create_app()

    @test_app.get("/test-error")
    def fail():
        raise RuntimeError("password=private_value")

    with caplog.at_level(logging.INFO, logger="architect.main"):
        response = TestClient(test_app).get(
            "/test-error", headers={"Origin": "http://localhost:5173"}
        )
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers["X-Request-ID"]
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "private_value" not in caplog.text


def test_application_shutdown_disposes_connections() -> None:
    with patch("architect.main.dispose_engine") as dispose:
        with TestClient(create_app()) as running_client:
            assert running_client.get("/health/live").status_code == 200
        dispose.assert_called_once()
