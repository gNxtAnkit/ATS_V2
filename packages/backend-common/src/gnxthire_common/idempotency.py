from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{16,255}$")


class IdempotencyStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class IdempotencyKey(BaseModel):
    value: str = Field(min_length=16, max_length=255)

    @field_validator("value")
    @classmethod
    def validate_safe_characters(cls, value: str) -> str:
        if not IDEMPOTENCY_KEY_PATTERN.fullmatch(value):
            raise ValueError("idempotency key contains unsupported characters")
        return value


class ResponseSnapshot(BaseModel):
    status_code: int = Field(ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    body_hash: str = Field(min_length=64, max_length=64)


class IdempotencyRecord(BaseModel):
    key: IdempotencyKey
    tenant_id: UUID | None = None
    actor_id: UUID | None = None
    request_fingerprint: str = Field(min_length=64, max_length=64)
    status: IdempotencyStatus
    response_snapshot: ResponseSnapshot | None = None


class IdempotencyRepository(Protocol):
    def get(self, key: IdempotencyKey) -> IdempotencyRecord | None:
        """Return an existing idempotency record without creating service-specific behavior."""
        ...

    def create_started(self, record: IdempotencyRecord) -> None:
        """Persist a started record using the caller service's transaction boundary."""
        ...

    def mark_completed(self, key: IdempotencyKey, snapshot: ResponseSnapshot) -> None:
        """Attach the response snapshot after the caller's operation succeeds."""
        ...


def hash_request_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def fingerprint_request(method: str, path: str, body: bytes, *, tenant_id: UUID | None = None) -> str:
    payload = {
        "body_hash": hash_request_body(body),
        "method": method.upper(),
        "path": path,
        "tenant_id": str(tenant_id) if tenant_id is not None else None,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def snapshot_response(status_code: int, headers: dict[str, str], body: bytes) -> ResponseSnapshot:
    return ResponseSnapshot(status_code=status_code, headers=headers, body_hash=hash_request_body(body))


def normalize_idempotency_key(raw_key: str) -> IdempotencyKey:
    return IdempotencyKey(value=raw_key.strip())
