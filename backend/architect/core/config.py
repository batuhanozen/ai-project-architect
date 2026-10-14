from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    database_url: SecretStr | None = None
    postgres_host: str = Field(default="localhost", min_length=1)
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = Field(default="architect", min_length=1)
    postgres_user: str = Field(default="architect", min_length=1)
    postgres_password: SecretStr | None = None
    db_connect_timeout_seconds: int = Field(default=2, ge=2, le=30)
    db_pool_timeout_seconds: int = Field(default=2, ge=1, le=30)
    db_statement_timeout_ms: int = Field(default=2000, ge=100, le=30000)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @model_validator(mode="after")
    def validate_database(self) -> "Settings":
        if self.database_url is not None:
            try:
                url = make_url(self.database_url.get_secret_value())
                valid = url.drivername == "postgresql+psycopg" and bool(url.database)
                valid = valid and (url.host is not None or "host" in url.query)
                # Accessing the port also validates its numeric representation.
                valid = valid and (url.port is None or 1 <= url.port <= 65535)
            except (ArgumentError, ValueError):
                valid = False
            if not valid:
                raise ValueError("DATABASE_URL must specify a postgresql+psycopg host and database")
        elif self.postgres_password is None or not self.postgres_password.get_secret_value():
            raise ValueError("Set DATABASE_URL or POSTGRES_PASSWORD")
        return self

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        for origin in (item.strip() for item in value.split(",") if item.strip()):
            try:
                url = urlsplit(origin)
                valid = (
                    url.scheme in {"http", "https"}
                    and bool(url.hostname)
                    and "*" not in (url.hostname or "")
                    and url.username is None
                    and url.password is None
                    and not (url.path or url.query or url.fragment)
                    and (url.port is None or 1 <= url.port <= 65535)
                )
            except ValueError:
                valid = False
            if not valid:
                raise ValueError("CORS_ORIGINS must contain explicit HTTP(S) origins without paths")
        return value

    @property
    def sqlalchemy_url(self) -> URL:
        if self.database_url is not None:
            return make_url(self.database_url.get_secret_value())
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value() if self.postgres_password else None,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
