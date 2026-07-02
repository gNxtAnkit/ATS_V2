from uuid import uuid4

import pytest

from gnxthire_common.errors import FieldError, ValidationFailure, build_error_envelope
from gnxthire_common.idempotency import (
    IdempotencyStatus,
    fingerprint_request,
    hash_request_body,
    normalize_idempotency_key,
    snapshot_response,
)
from gnxthire_common.pagination import (
    CursorPayload,
    build_cursor_page,
    decode_cursor,
    encode_cursor,
)


def test_error_envelope_shape_is_stable() -> None:
    envelope = build_error_envelope(
        request_id="req_123",
        code="validation_failed",
        message="Invalid request",
        field_errors=[FieldError(field="email", message="Invalid email")],
    )

    assert envelope.model_dump() == {
        "error": {
            "request_id": "req_123",
            "code": "validation_failed",
            "message": "Invalid request",
            "field_errors": [{"field": "email", "message": "Invalid email", "code": "invalid"}],
        },
    }


def test_cursor_round_trip() -> None:
    payload = CursorPayload(sort_value="2026-07-01T00:00:00+00:00", entity_id=uuid4())

    encoded = encode_cursor(payload)

    assert decode_cursor(encoded) == payload


def test_invalid_cursor_raises_validation_failure() -> None:
    with pytest.raises(ValidationFailure):
        decode_cursor("not-a-valid-cursor")


def test_cursor_page_shape_is_stable() -> None:
    next_payload = CursorPayload(sort_value="2026-07-01T00:00:00+00:00", entity_id=uuid4())

    page = build_cursor_page(["item"], limit=1, next_payload=next_payload)

    assert page.data == ["item"]
    assert page.next_cursor is not None
    assert page.has_more is True


def test_idempotency_helpers_normalize_and_hash() -> None:
    key = normalize_idempotency_key("  abcdefghijklmnop  ")

    assert key.value == "abcdefghijklmnop"
    assert hash_request_body(b'{"ok":true}') == hash_request_body(b'{"ok":true}')


def test_idempotency_key_rejects_unsafe_characters() -> None:
    with pytest.raises(ValueError, match="unsupported characters"):
        normalize_idempotency_key("abcdefghijklmnop unsafe")


def test_request_fingerprint_and_response_snapshot_are_stable() -> None:
    tenant_id = uuid4()
    first = fingerprint_request("post", "/v1/example", b'{"a":1}', tenant_id=tenant_id)
    second = fingerprint_request("POST", "/v1/example", b'{"a":1}', tenant_id=tenant_id)
    snapshot = snapshot_response(201, {"content-type": "application/json"}, b'{"ok":true}')

    assert first == second
    assert snapshot.status_code == 201
    assert snapshot.body_hash == hash_request_body(b'{"ok":true}')
    assert IdempotencyStatus.STARTED.value == "started"
