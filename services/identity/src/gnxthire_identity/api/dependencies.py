from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from gnxthire_common.db import create_session_factory, create_sync_engine, session_scope
from gnxthire_common.errors import AuthenticationError
from gnxthire_common.rls import set_platform_admin_context, set_tenant_context

from gnxthire_identity.config import IdentitySettings, get_identity_settings
from gnxthire_identity.email import SmtpEmailSender
from gnxthire_identity.platform_admin.repository import PlatformAdminRepository, PlatformUserRecord
from gnxthire_identity.platform_admin.service import PlatformAdminIdentityService
from gnxthire_identity.rate_limit import MemoryRateLimiter, RateLimiter, RedisRateLimiter
from gnxthire_identity.request_metadata import RequestMetadata
from gnxthire_identity.security import verify_signed_token
from gnxthire_identity.tenant.repository import TenantIdentityRepository, TenantUserRecord
from gnxthire_identity.tenant.service import TenantIdentityService

bearer = HTTPBearer(auto_error=False)
_engine = create_sync_engine()
_session_factory = create_session_factory(_engine)
_local_rate_limiter = MemoryRateLimiter()


def session_dependency() -> Iterator[Session]:
    with session_scope(_session_factory) as session:
        yield session


def request_metadata(
    request: Request,
    x_request_id: str | None = Header(default=None),
    x_correlation_id: str | None = Header(default=None),
) -> RequestMetadata:
    request_id = x_request_id or "missing-request-id"
    return RequestMetadata(
        request_id=request_id,
        correlation_id=x_correlation_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def rate_limiter_for_settings(settings: IdentitySettings) -> RateLimiter:
    if settings.rate_limit_backend == "memory":
        return _local_rate_limiter
    return RedisRateLimiter(Redis.from_url(settings.redis_url))


# -- Tenant realm ------------------------------------------------------------------------


def tenant_identity_service(
    session: Session = Depends(session_dependency),
    settings: IdentitySettings = Depends(get_identity_settings),
) -> TenantIdentityService:
    return TenantIdentityService(
        repository=TenantIdentityRepository(session),
        settings=settings,
        email_sender=SmtpEmailSender(settings),
        rate_limiter=rate_limiter_for_settings(settings),
    )


def authenticated_tenant_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(session_dependency),
    settings: IdentitySettings = Depends(get_identity_settings),
) -> tuple[TenantUserRecord, TenantIdentityRepository, IdentitySettings]:
    if credentials is None:
        raise AuthenticationError("Authentication required", safe_detail="Authentication required")
    payload = verify_signed_token(
        credentials.credentials,
        secret=settings.access_token_secret.get_secret_value(),
        issuer=settings.token_issuer,
        audience=settings.tenant_audience,
        token_type="access",
    )
    tenant_id = UUID(payload["tid"])
    user_id = UUID(payload["sub"])
    repository = TenantIdentityRepository(session)
    set_tenant_context(
        session,
        request_id="authenticated-request",
        tenant_id=tenant_id,
        actor_id=user_id,
    )
    user = repository.get_tenant_user_by_id(tenant_id, user_id)
    if user is None or user.status not in {"active", "invited"}:
        raise AuthenticationError("Authentication required", safe_detail="Authentication required")
    return user, repository, settings


def require_tenant_user(
    authenticated: tuple[TenantUserRecord, TenantIdentityRepository, IdentitySettings] = Depends(authenticated_tenant_user),
) -> tuple[TenantUserRecord, TenantIdentityRepository, IdentitySettings]:
    return authenticated


# -- Platform-admin realm -----------------------------------------------------------------


def platform_admin_identity_service(
    session: Session = Depends(session_dependency),
    settings: IdentitySettings = Depends(get_identity_settings),
) -> PlatformAdminIdentityService:
    return PlatformAdminIdentityService(
        repository=PlatformAdminRepository(session),
        settings=settings,
        email_sender=SmtpEmailSender(settings),
        rate_limiter=rate_limiter_for_settings(settings),
    )


def authenticated_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(session_dependency),
    settings: IdentitySettings = Depends(get_identity_settings),
) -> tuple[PlatformUserRecord, PlatformAdminRepository, IdentitySettings]:
    if credentials is None:
        raise AuthenticationError("Authentication required", safe_detail="Authentication required")
    payload = verify_signed_token(
        credentials.credentials,
        secret=settings.access_token_secret.get_secret_value(),
        issuer=settings.token_issuer,
        audience=settings.platform_admin_audience,
        token_type="access",
    )
    user_id = UUID(payload["sub"])
    repository = PlatformAdminRepository(session)
    # Platform admin auth never sets tenant context: no tenant_id is ever present on
    # a platform-admin token, and set_platform_admin_context never touches
    # app.current_tenant_id, so tenant-scoped RLS is never satisfied by this actor
    # unless a tenant_id is explicitly supplied for an audited support session
    # (not implemented here; out of Phase 2 scope).
    set_platform_admin_context(session, request_id="authenticated-request", platform_admin_id=user_id)
    user = repository.get_platform_user_by_id(user_id)
    if user is None or user.status != "active":
        raise AuthenticationError("Authentication required", safe_detail="Authentication required")
    return user, repository, settings


def require_platform_admin(
    authenticated: tuple[PlatformUserRecord, PlatformAdminRepository, IdentitySettings] = Depends(
        authenticated_platform_admin
    ),
) -> tuple[PlatformUserRecord, PlatformAdminRepository, IdentitySettings]:
    return authenticated


def optional_authenticated_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(session_dependency),
    settings: IdentitySettings = Depends(get_identity_settings),
) -> tuple[TenantUserRecord, TenantIdentityRepository, IdentitySettings] | tuple[
    PlatformUserRecord, PlatformAdminRepository, IdentitySettings
] | None:
    """Returns the authenticated actor (tenant or platform-admin) if a valid bearer
    token is present, otherwise None. No route currently requires this; included for
    completeness so future endpoints that behave differently for anonymous vs.
    authenticated callers do not need to invent their own token-probing logic."""
    if credentials is None:
        return None
    try:
        return authenticated_tenant_user(credentials, session, settings)
    except AuthenticationError:
        pass
    try:
        return authenticated_platform_admin(credentials, session, settings)
    except AuthenticationError:
        return None
