from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestMetadata:
    request_id: str
    correlation_id: str | None
    ip_address: str | None
    user_agent: str | None
