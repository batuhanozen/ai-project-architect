import os
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, Uuid, create_engine, insert, inspect, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from architect.core.config import get_settings
from architect.db.models import Project
from architect.db.session import get_engine
from architect.main import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires RUN_DB_TESTS=1"),
]


def test_project_table_round_trip() -> None:
    project_id = uuid.uuid4()
    with get_engine().connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                insert(Project).values(
                    id=project_id, name="Sample project", description="A test idea"
                )
            )
            project = connection.execute(
                select(Project.id, Project.name, Project.created_at).where(Project.id == project_id)
            ).one()
            assert project.id == project_id
            assert project.name == "Sample project"
            assert project.created_at is not None
            assert project.created_at.tzinfo is not None
        finally:
            transaction.rollback()


def test_migrated_schema_matches_required_columns_and_primary_key() -> None:
    inspector = inspect(get_engine())
    columns = {column["name"]: column for column in inspector.get_columns("projects")}
    assert set(columns) == {"id", "name", "description", "created_at", "updated_at"}
    assert all(not column["nullable"] for column in columns.values())
    assert isinstance(columns["id"]["type"], Uuid)
    assert columns["name"]["type"].length == 160
    for name in ("created_at", "updated_at"):
        assert isinstance(columns[name]["type"], DateTime)
        assert columns[name]["type"].timezone
        assert columns[name]["default"] is not None
    assert inspector.get_pk_constraint("projects")["constrained_columns"] == ["id"]


def test_database_enforces_required_description() -> None:
    with get_engine().connect() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(insert(Project).values(name="Missing description", description=None))
        connection.rollback()


def test_readiness_against_migrated_postgresql() -> None:
    assert TestClient(app).get("/health/ready").status_code == 200


def test_readiness_rejects_unmigrated_schema() -> None:
    schema = "unmigrated_" + uuid.uuid4().hex
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    empty_engine = create_engine(
        get_settings().sqlalchemy_url,
        connect_args={"options": f"-c search_path={schema}", "connect_timeout": 2},
    )
    try:
        with patch("architect.api.health.get_engine", return_value=empty_engine):
            response = TestClient(app).get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
    finally:
        empty_engine.dispose()
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}"'))


def test_failed_postgresql_authentication_returns_safe_error() -> None:
    invalid_engine = create_engine(
        get_settings().sqlalchemy_url.set(password="deliberately_invalid_test_password"),
        connect_args={"connect_timeout": 2},
    )
    try:
        with patch("architect.api.health.get_engine", return_value=invalid_engine):
            response = TestClient(app).get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
        assert TestClient(app).get("/health/live").status_code == 200
    finally:
        invalid_engine.dispose()


def test_database_statement_timeout_and_connection_recovery() -> None:
    with get_engine().connect() as connection:
        timeout_ms = connection.scalar(
            text("SELECT setting::int FROM pg_settings WHERE name = 'statement_timeout'")
        )
        assert timeout_ms == get_settings().db_statement_timeout_ms
        with pytest.raises(DBAPIError):
            connection.execute(
                text("SELECT pg_sleep(:seconds)"), {"seconds": timeout_ms / 1000 + 1}
            )
        connection.rollback()
        assert connection.scalar(text("SELECT 1")) == 1
