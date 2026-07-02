from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvironmentName = Literal["local", "test", "dev", "qa", "staging", "production"]
LogLevelName = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GNXTHIRE_", env_file=".env", extra="ignore")

    app_name: str = Field(default="gNxtHire", min_length=1)
    environment: EnvironmentName = Field(
        default="local",
        validation_alias=AliasChoices("GNXTHIRE_ENVIRONMENT", "GNXTHIRE_ENV"),
    )
    service_name: str = Field(default="service-shell", min_length=1)
    version: str = Field(default="0.0.0-phase1", min_length=1)
    debug: bool = False
    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://gnxthire:gnxthire_local_password@localhost:45432/gnxthire_local",
        validation_alias=AliasChoices("DATABASE_URL", "GNXTHIRE_DATABASE_URL"),
    )
    test_database_url: PostgresDsn | None = Field(
        default=None,
        validation_alias=AliasChoices("TEST_DATABASE_URL", "GNXTHIRE_TEST_DATABASE_URL"),
    )
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "GNXTHIRE_REDIS_URL"),
    )
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias=AliasChoices("KAFKA_BOOTSTRAP_SERVERS", "GNXTHIRE_KAFKA_BOOTSTRAP_SERVERS"),
    )
    opensearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias=AliasChoices("OPENSEARCH_URL", "GNXTHIRE_OPENSEARCH_URL"),
    )
    database_echo: bool = False
    logging_level: LogLevelName = "INFO"
    request_id_header: str = "x-request-id"
    correlation_id_header: str = "x-correlation-id"
    enforce_rls_context: bool = True
    run_migrations_on_startup: bool = False
    run_database_validation_on_startup: bool = False
    auth_jwt_issuer: str | None = None
    auth_jwt_audience: str | None = None

    @field_validator("database_url", "test_database_url", "redis_url", "opensearch_url", mode="before")
    @classmethod
    def strip_wrapping_quotes(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().strip("\"'")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        if self.environment != "production":
            return self

        missing = [
            name
            for name in ("DATABASE_URL", "REDIS_URL")
            if name not in os.environ and f"GNXTHIRE_{name}" not in os.environ
        ]
        if missing:
            raise ValueError(f"production settings require explicit environment values: {', '.join(missing)}")
        if self.debug:
            raise ValueError("production settings cannot enable debug")
        if self.database_echo:
            raise ValueError("production settings cannot enable SQL echo")
        if _is_local_database_url(str(self.database_url)):
            raise ValueError("production database_url must not point at a local database")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def _is_local_database_url(database_url: str) -> bool:
    parsed = urlparse(database_url)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}
