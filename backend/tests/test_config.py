import pytest
from pydantic import ValidationError

from architect.core.config import Settings


def test_separate_credentials_preserve_special_characters() -> None:
    password = "local@pass:/%?#"
    settings = Settings(database_url=None, postgres_password=password, _env_file=None)
    assert settings.sqlalchemy_url.password == password
    assert password not in repr(settings)
    assert password not in settings.model_dump_json()


def test_database_url_takes_precedence_and_is_redacted() -> None:
    url = "postgresql+psycopg://operator:private_password@localhost/example"
    settings = Settings(database_url=url, postgres_password="other", _env_file=None)
    assert settings.sqlalchemy_url.database == "example"
    assert "private_password" not in repr(settings)


@pytest.mark.parametrize("url", ["sqlite:///local.db", "not-a-url", "postgresql://host/db"])
def test_invalid_database_configuration_fails_early(url: str) -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL must"):
        Settings(database_url=url, _env_file=None)


def test_credentials_are_required() -> None:
    with pytest.raises(ValidationError, match="Set DATABASE_URL or POSTGRES_PASSWORD"):
        Settings(database_url=None, postgres_password=None, _env_file=None)


@pytest.mark.parametrize(
    "origin", ["*", "https://*.example.com", "https://example.com/path", "https://user:secret@host"]
)
def test_cors_configuration_rejects_unsafe_or_invalid_origins(origin: str) -> None:
    with pytest.raises(ValidationError) as error:
        Settings(cors_origins=origin, _env_file=None)
    assert "secret" not in str(error.value)


def test_timeout_configuration_is_bounded() -> None:
    with pytest.raises(ValidationError):
        Settings(db_connect_timeout_seconds=0, _env_file=None)
