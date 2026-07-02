from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from gnxthire_common.context import ActorType, RequestContext
from gnxthire_common.errors import PlatformContextRequired, TenantContextRequired
from gnxthire_common.logging import REDACTED_VALUE, context_log_fields, log_extra, redact_mapping
from gnxthire_common.migrations import assert_required_schema_files
from gnxthire_common.rls import (
    clear_context,
    require_platform_admin_context,
    require_tenant_context,
    set_platform_admin_context,
    set_tenant_context,
)


class CapturingSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, statement: Any, parameters: dict[str, str]) -> None:
        self.calls.append({"statement": str(statement), "parameters": parameters})


def test_redaction_removes_sensitive_values_recursively() -> None:
    values = {
        "email": "safe@example.com",
        "password": "secret",
        "nested": {"api_key": "secret-key"},
        "items": [{"session_token": "token"}],
    }

    redacted = redact_mapping(values)

    assert redacted["email"] == "safe@example.com"
    assert redacted["password"] == REDACTED_VALUE
    assert redacted["nested"]["api_key"] == REDACTED_VALUE
    assert redacted["items"][0]["session_token"] == REDACTED_VALUE


def test_rls_context_guards_separate_tenant_and_platform_admin() -> None:
    tenant_context = RequestContext(
        request_id="req_1",
        tenant_id=uuid4(),
        actor_id=uuid4(),
        actor_type=ActorType.TENANT_USER,
    )
    platform_context = RequestContext(
        request_id="req_2",
        actor_id=uuid4(),
        actor_type=ActorType.PLATFORM_USER,
        is_platform_admin=True,
        platform_admin_id=uuid4(),
    )

    require_tenant_context(tenant_context)
    require_platform_admin_context(platform_context)

    with pytest.raises(TenantContextRequired):
        require_tenant_context(platform_context)
    with pytest.raises(PlatformContextRequired):
        require_platform_admin_context(tenant_context)


def test_required_schema_files_are_present() -> None:
    schema_directory = Path(__file__).resolve().parents[2] / "db" / "schema"

    assert_required_schema_files(schema_directory)


def test_set_tenant_context_uses_transaction_local_database_settings() -> None:
    session = CapturingSession()
    tenant_id = uuid4()
    actor_id = uuid4()

    context = set_tenant_context(
        session,  # type: ignore[arg-type]
        request_id="req_1",
        tenant_id=tenant_id,
        actor_id=actor_id,
        permissions=("tenant.read",),
    )

    captured = {call["parameters"]["key"]: call["parameters"]["value"] for call in session.calls}
    assert context.tenant_id == tenant_id
    assert captured["app.current_tenant_id"] == str(tenant_id)
    assert captured["app.user_id"] == str(actor_id)
    assert captured["app.is_platform_admin"] == "false"
    assert captured["app.permissions"] == "tenant.read"


def test_platform_admin_context_is_explicit_and_clearable() -> None:
    session = CapturingSession()
    platform_admin_id = uuid4()

    context = set_platform_admin_context(
        session,  # type: ignore[arg-type]
        request_id="req_admin",
        platform_admin_id=platform_admin_id,
    )
    clear_context(session)  # type: ignore[arg-type]

    captured = {call["parameters"]["key"]: call["parameters"]["value"] for call in session.calls}
    assert context.is_platform_admin is True
    assert context.platform_admin_id == platform_admin_id
    assert captured["app.platform_admin_id"] == ""
    assert captured["app.is_platform_admin"] == ""


def test_log_helpers_redact_structured_context() -> None:
    context = RequestContext(
        request_id="req_3",
        tenant_id=uuid4(),
        actor_id=uuid4(),
        actor_type=ActorType.TENANT_USER,
    )

    fields = context_log_fields(context)
    extra = log_extra({"request": fields, "authorization": "Bearer token"})

    assert extra["structured"]["request"]["request_id"] == "req_3"
    assert extra["structured"]["authorization"] == REDACTED_VALUE
