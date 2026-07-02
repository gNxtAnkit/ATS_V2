from __future__ import annotations

import base64
import binascii
import json
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from gnxthire_common.errors import ValidationFailure

T = TypeVar("T")


class CursorPayload(BaseModel):
    sort_value: str = Field(min_length=1)
    entity_id: UUID


class PageRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    cursor: str | None = None


class PageInfo(BaseModel):
    next_cursor: str | None
    has_next_page: bool


class CursorPage(BaseModel, Generic[T]):
    data: list[T]
    next_cursor: str | None
    has_more: bool


def encode_cursor(payload: CursorPayload) -> str:
    raw_payload = payload.model_dump(mode="json")
    encoded = base64.urlsafe_b64encode(json.dumps(raw_payload, separators=(",", ":")).encode("utf-8"))
    return encoded.decode("ascii")


def decode_cursor(cursor: str) -> CursorPayload:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii"))
        return CursorPayload.model_validate_json(decoded)
    except (ValueError, binascii.Error) as exc:
        raise ValidationFailure("Invalid pagination cursor", safe_detail="Invalid pagination cursor") from exc


def build_cursor_page(items: list[T], *, limit: int, next_payload: CursorPayload | None) -> CursorPage[T]:
    return CursorPage(
        data=items,
        next_cursor=encode_cursor(next_payload) if next_payload is not None else None,
        has_more=len(items) >= limit and next_payload is not None,
    )


def utc_now_cursor_value() -> str:
    return datetime.now(UTC).isoformat()
