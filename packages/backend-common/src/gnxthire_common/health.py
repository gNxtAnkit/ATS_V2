from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import Engine, text


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class HealthCheckResult(BaseModel):
    name: str = Field(min_length=1)
    status: HealthStatus
    detail: str | None = None


class AppHealthResult(BaseModel):
    service_name: str = Field(min_length=1)
    status: HealthStatus
    checks: list[HealthCheckResult] = Field(default_factory=list)


class RedisPingClient(Protocol):
    def ping(self) -> Any:
        """Return a truthy value when Redis is reachable."""
        ...


def aggregate_health(service_name: str, checks: list[HealthCheckResult]) -> AppHealthResult:
    if any(check.status == HealthStatus.DOWN for check in checks):
        status = HealthStatus.DOWN
    elif any(check.status == HealthStatus.DEGRADED for check in checks):
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.OK
    return AppHealthResult(service_name=service_name, status=status, checks=checks)


def database_health_check(engine: Engine) -> HealthCheckResult:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        return HealthCheckResult(name="database", status=HealthStatus.DOWN, detail=str(exc))
    return HealthCheckResult(name="database", status=HealthStatus.OK)


def redis_health_check(client: RedisPingClient | None) -> HealthCheckResult:
    if client is None:
        return HealthCheckResult(name="redis", status=HealthStatus.DEGRADED, detail="Redis client not configured")
    try:
        client.ping()
    except Exception as exc:
        return HealthCheckResult(name="redis", status=HealthStatus.DOWN, detail=str(exc))
    return HealthCheckResult(name="redis", status=HealthStatus.OK)
