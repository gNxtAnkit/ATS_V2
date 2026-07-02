from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from gnxthire_common.context import ActorType, RequestContext
from gnxthire_common.errors import PlatformContextRequired, TenantContextRequired

APP_CONTEXT_KEYS = (
    "app.current_tenant_id",
    "app.user_id",
    "app.actor_type",
    "app.is_platform_admin",
    "app.platform_admin_id",
    "app.permissions",
    "app.request_id",
    "app.correlation_id",
)


def require_tenant_context(context: RequestContext) -> None:
    if context.tenant_id is None or context.is_platform_admin:
        raise TenantContextRequired("tenant-facing database access requires tenant context")


def require_platform_admin_context(context: RequestContext) -> None:
    if not context.is_platform_admin:
        raise PlatformContextRequired("platform-admin database access requires explicit platform context")


def set_tenant_context(
    session: Session,
    *,
    request_id: str,
    tenant_id: UUID,
    actor_id: UUID,
    actor_type: ActorType = ActorType.TENANT_USER,
    correlation_id: str | None = None,
    permissions: tuple[str, ...] = (),
) -> RequestContext:
    context = RequestContext(
        request_id=request_id,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_type=actor_type,
        permissions=permissions,
    )
    require_tenant_context(context)
    apply_rls_context(session, context)
    return context


def set_platform_admin_context(
    session: Session,
    *,
    request_id: str,
    platform_admin_id: UUID,
    correlation_id: str | None = None,
    tenant_id: UUID | None = None,
    permissions: tuple[str, ...] = (),
) -> RequestContext:
    context = RequestContext(
        request_id=request_id,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        actor_id=platform_admin_id,
        actor_type=ActorType.PLATFORM_USER,
        is_platform_admin=True,
        platform_admin_id=platform_admin_id,
        permissions=permissions,
    )
    require_platform_admin_context(context)
    apply_rls_context(session, context)
    return context


def apply_rls_context(session: Session, context: RequestContext) -> None:
    tenant_id = "" if context.tenant_id is None else str(context.tenant_id)
    actor_id = "" if context.actor_id is None else str(context.actor_id)
    platform_admin_id = "" if context.platform_admin_id is None else str(context.platform_admin_id)
    permissions = ",".join(context.permissions)
    values = {
        "app.current_tenant_id": tenant_id,
        "app.user_id": actor_id,
        "app.actor_type": context.actor_type.value,
        "app.is_platform_admin": "true" if context.is_platform_admin else "false",
        "app.platform_admin_id": platform_admin_id,
        "app.permissions": permissions,
        "app.request_id": context.request_id,
        "app.correlation_id": context.effective_correlation_id,
    }
    for key, value in values.items():
        _set_local_config(session, key, value)


def clear_context(session: Session) -> None:
    for key in APP_CONTEXT_KEYS:
        _set_local_config(session, key, "")


def _set_local_config(session: Session, key: str, value: str) -> None:
    session.execute(
        text("SELECT set_config(:key, :value, true)"),
        {"key": key, "value": value},
    )
