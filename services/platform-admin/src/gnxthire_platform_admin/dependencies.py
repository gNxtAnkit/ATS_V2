from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from gnxthire_common.db import create_session_factory, create_sync_engine, session_scope
from gnxthire_common.errors import AuthenticationError, AuthorizationError
from gnxthire_common.rls import set_platform_admin_context
from gnxthire_identity.config import IdentitySettings, get_identity_settings
from gnxthire_identity.security import verify_signed_token


bearer = HTTPBearer(auto_error=False)
_engine = create_sync_engine()
_session_factory = create_session_factory(_engine)


@dataclass(frozen=True)
class RequestMetadata:
    request_id: str
    correlation_id: str | None
    ip_address: str | None
    user_agent: str | None


@dataclass(frozen=True)
class PlatformAdminActorContext:
    platform_user_id: UUID
    email: str
    display_name: str
    status: str
    permissions: frozenset[str]
    role_keys: frozenset[str]
    session_id: UUID | None

    def has_permission(self, permission_key: str) -> bool:
        return permission_key in self.permissions


def session_dependency() -> Iterator[Session]:
    with session_scope(_session_factory) as session:
        yield session


def request_metadata(
    request: Request,
    x_request_id: str | None = Header(default=None),
    x_correlation_id: str | None = Header(default=None),
) -> RequestMetadata:
    return RequestMetadata(
        request_id=x_request_id or "missing-request-id",
        correlation_id=x_correlation_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _try_verify_tenant_token(token: str, settings: IdentitySettings) -> bool:
    try:
        verify_signed_token(
            token,
            secret=settings.access_token_secret.get_secret_value(),
            issuer=settings.token_issuer,
            audience=settings.tenant_audience,
            token_type="access",
        )
    except AuthenticationError:
        return False
    return True


def _load_actor(
    session: Session,
    *,
    platform_user_id: UUID,
    session_id: UUID | None,
    metadata: RequestMetadata,
) -> PlatformAdminActorContext:
    user = session.execute(
        text(
            """
            SELECT id, email::text AS email, display_name, status::text AS status
            FROM platform.platform_users
            WHERE id = :id AND deleted_at IS NULL
            """
        ),
        {"id": platform_user_id},
    ).mappings().one_or_none()
    if user is None:
        raise AuthenticationError("Authentication required", safe_detail="Authentication required")
    if user["status"] != "active":
        raise AuthorizationError("Platform admin is not active", safe_detail="Platform admin is not active")

    role_rows = session.execute(
        text(
            """
            SELECT r.id, r.role_key::text AS role_key
            FROM platform.platform_user_roles ur
            JOIN platform.platform_roles r ON r.id = ur.role_id
            WHERE ur.platform_user_id = :id
            """
        ),
        {"id": platform_user_id},
    ).mappings().all()
    role_keys = frozenset(row["role_key"] for row in role_rows)

    if "super_admin" in role_keys:
        permission_rows = session.execute(
            text("SELECT permission_key::text AS permission_key FROM platform.platform_permissions")
        ).mappings().all()
    else:
        permission_rows = session.execute(
            text(
                """
                SELECT DISTINCT p.permission_key::text AS permission_key
                FROM platform.platform_user_roles ur
                JOIN platform.platform_role_permissions rp ON rp.role_id = ur.role_id
                JOIN platform.platform_permissions p ON p.id = rp.permission_id
                WHERE ur.platform_user_id = :id
                """
            ),
            {"id": platform_user_id},
        ).mappings().all()
    permissions = frozenset(row["permission_key"] for row in permission_rows)
    set_platform_admin_context(
        session,
        request_id=metadata.request_id,
        platform_admin_id=platform_user_id,
        correlation_id=metadata.correlation_id,
        permissions=tuple(sorted(permissions)),
    )
    return PlatformAdminActorContext(
        platform_user_id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        status=user["status"],
        permissions=permissions,
        role_keys=role_keys,
        session_id=session_id,
    )


def require_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(session_dependency),
    settings: IdentitySettings = Depends(get_identity_settings),
    metadata: RequestMetadata = Depends(request_metadata),
) -> PlatformAdminActorContext:
    if credentials is None:
        raise AuthenticationError("Authentication required", safe_detail="Authentication required")
    token = credentials.credentials
    try:
        payload = verify_signed_token(
            token,
            secret=settings.access_token_secret.get_secret_value(),
            issuer=settings.token_issuer,
            audience=settings.platform_admin_audience,
            token_type="access",
        )
    except AuthenticationError as exc:
        if _try_verify_tenant_token(token, settings):
            raise AuthorizationError(
                "Tenant-user tokens cannot access Platform Admin APIs",
                safe_detail="Tenant-user tokens cannot access Platform Admin APIs",
            ) from exc
        raise AuthenticationError("Authentication required", safe_detail="Authentication required") from exc

    if payload.get("actor_type") != "platform_user" or payload.get("tid") is not None:
        raise AuthorizationError(
            "Only platform-admin tokens can access Platform Admin APIs",
            safe_detail="Only platform-admin tokens can access Platform Admin APIs",
        )
    session_id = UUID(payload["sid"]) if payload.get("sid") else None
    return _load_actor(
        session,
        platform_user_id=UUID(payload["sub"]),
        session_id=session_id,
        metadata=metadata,
    )


def require_platform_permission(permission_key: str) -> Callable[[PlatformAdminActorContext], PlatformAdminActorContext]:
    def _dependency(
        actor: PlatformAdminActorContext = Depends(require_platform_admin),
    ) -> PlatformAdminActorContext:
        if not actor.has_permission(permission_key):
            raise AuthorizationError("Missing platform permission", safe_detail="Missing platform permission")
        return actor

    return _dependency

