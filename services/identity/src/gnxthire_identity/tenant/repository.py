from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from gnxthire_common.context import ActorType
from gnxthire_common.rls import set_tenant_context

SYSTEM_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000000")


@dataclass(frozen=True)
class TenantRecord:
    id: UUID
    name: str
    status: str


@dataclass(frozen=True)
class TenantUserRecord:
    tenant_id: UUID
    id: UUID
    email: str
    display_name: str
    status: str
    password_hash: str | None
    email_verified_at: datetime | None


@dataclass(frozen=True)
class SessionRecord:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    session_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True)
class MfaFactorRecord:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    method: str
    secret_ref: str | None
    is_primary: bool
    disabled_at: datetime | None


class TenantIdentityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # -- Cross-tenant, pre-authentication lookups -----------------------------------
    #
    # `tenant.users` and its token tables are RLS-forced on tenant_id. Before a login
    # or a reset/verify token is resolved, the caller does not yet know which tenant
    # the email/token belongs to, so these queries must run with a temporary,
    # request-local `app.is_platform_admin` GUC override (satisfying the RLS policy's
    # `tenant_id = app.current_tenant_id() OR app.is_platform_admin()` predicate for
    # exactly one statement) rather than a real tenant/platform-admin RequestContext.
    # Every call site MUST follow this with `set_pre_auth_tenant_context` (once a
    # single tenant is resolved) so all further statements in the request run under
    # real tenant-scoped RLS. `set_config(..., true)` is transaction/session-local and
    # cannot leak across requests since each request gets its own session (see
    # gnxthire_common.db.session_scope).

    def set_cross_tenant_lookup_guc(self) -> None:
        self._session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))

    def find_active_tenant_users_by_email(self, email: str) -> list[TenantUserRecord]:
        self.set_cross_tenant_lookup_guc()
        rows = self._session.execute(
            text(
                """
                SELECT tenant_id, id, email::text AS email, display_name, status,
                       password_hash, email_verified_at
                FROM tenant.users
                WHERE email = :email AND status = 'active' AND deleted_at IS NULL
                """
            ),
            {"email": email},
        ).mappings().all()
        return [TenantUserRecord(**row) for row in rows]

    def find_tenant_users_by_email(self, email: str) -> list[TenantUserRecord]:
        """Broader than find_active_tenant_users_by_email: includes invited/locked/suspended
        users (excludes only soft-deleted), for password-reset/email-verification flows where
        a not-yet-active (invited, pending first verification) user must still be resolvable."""
        self.set_cross_tenant_lookup_guc()
        rows = self._session.execute(
            text(
                """
                SELECT tenant_id, id, email::text AS email, display_name, status,
                       password_hash, email_verified_at
                FROM tenant.users
                WHERE email = :email AND deleted_at IS NULL
                """
            ),
            {"email": email},
        ).mappings().all()
        return [TenantUserRecord(**row) for row in rows]

    def consume_password_reset_token_global(self, token_hmac: str) -> tuple[UUID, UUID] | None:
        self.set_cross_tenant_lookup_guc()
        row = self._session.execute(
            text(
                """
                UPDATE tenant.password_reset_tokens
                SET status = 'used', used_at = now()
                WHERE token_hmac = :token_hmac AND status = 'pending' AND expires_at > now()
                RETURNING tenant_id, user_id
                """
            ),
            {"token_hmac": token_hmac},
        ).one_or_none()
        return (row.tenant_id, row.user_id) if row else None

    def consume_email_verification_token_global(self, token_hmac: str) -> tuple[UUID, UUID] | None:
        self.set_cross_tenant_lookup_guc()
        row = self._session.execute(
            text(
                """
                UPDATE tenant.email_verification_tokens
                SET status = 'used', used_at = now()
                WHERE token_hmac = :token_hmac AND status = 'pending' AND expires_at > now()
                RETURNING tenant_id, user_id
                """
            ),
            {"token_hmac": token_hmac},
        ).one_or_none()
        return (row.tenant_id, row.user_id) if row else None

    def write_platform_audit_log(
        self,
        *,
        tenant_id: UUID | None,
        actor_type: str,
        action_key: str,
        object_schema: str,
        object_table: str,
        object_id: UUID | None,
        after_state: dict[str, object] | None,
        ip_address: str | None,
        user_agent: str | None,
        request_id: str | None,
    ) -> None:
        self._session.execute(
            text(
                """
                INSERT INTO platform.audit_logs (
                  tenant_id, actor_type, action_key, object_schema, object_table, object_id,
                  after_state, ip_address, user_agent, request_id
                ) VALUES (
                  :tenant_id, :actor_type, :action_key, :object_schema, :object_table, :object_id,
                  CAST(:after_state AS jsonb), CAST(:ip_address AS inet), :user_agent, :request_id
                )
                """
            ),
            {
                "tenant_id": tenant_id,
                "actor_type": actor_type,
                "action_key": action_key,
                "object_schema": object_schema,
                "object_table": object_table,
                "object_id": object_id,
                "after_state": json.dumps(after_state or {}),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id,
            },
        )

    # -- Tenant resolution & authenticated (RLS-scoped) operations -------------------

    def resolve_tenant_by_id(self, tenant_id: UUID) -> TenantRecord | None:
        row = self._session.execute(
            text("SELECT id, name, status FROM platform.tenants WHERE id = :tenant_id AND deleted_at IS NULL"),
            {"tenant_id": tenant_id},
        ).mappings().one_or_none()
        return TenantRecord(**row) if row else None

    def set_pre_auth_tenant_context(self, *, tenant_id: UUID, request_id: str) -> None:
        set_tenant_context(
            self._session,
            request_id=request_id,
            tenant_id=tenant_id,
            actor_id=SYSTEM_ACTOR_ID,
            actor_type=ActorType.SYSTEM,
        )

    def get_tenant_user_by_email(self, tenant_id: UUID, email: str) -> TenantUserRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT tenant_id, id, email::text AS email, display_name, status,
                       password_hash, email_verified_at
                FROM tenant.users
                WHERE tenant_id = :tenant_id
                  AND email = :email
                  AND deleted_at IS NULL
                LIMIT 1
                """
            ),
            {"tenant_id": tenant_id, "email": email},
        ).mappings().one_or_none()
        return TenantUserRecord(**row) if row else None

    def get_tenant_user_by_id(self, tenant_id: UUID, user_id: UUID) -> TenantUserRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT tenant_id, id, email::text AS email, display_name, status,
                       password_hash, email_verified_at
                FROM tenant.users
                WHERE tenant_id = :tenant_id
                  AND id = :user_id
                  AND deleted_at IS NULL
                LIMIT 1
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        ).mappings().one_or_none()
        return TenantUserRecord(**row) if row else None

    def update_last_login(self, tenant_id: UUID, user_id: UUID) -> None:
        self._session.execute(
            text("UPDATE tenant.users SET last_login_at = now() WHERE tenant_id = :tenant_id AND id = :user_id"),
            {"tenant_id": tenant_id, "user_id": user_id},
        )

    def update_password(self, tenant_id: UUID, user_id: UUID, password_hash: str) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.users
                SET password_hash = :password_hash, updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :user_id
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id, "password_hash": password_hash},
        )

    def mark_email_verified(self, tenant_id: UUID, user_id: UUID) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.users
                SET email_verified_at = COALESCE(email_verified_at, now()), updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :user_id
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )

    def count_recent_failed_logins(self, tenant_id: UUID, user_id: UUID, *, window_minutes: int) -> int:
        row = self._session.execute(
            text(
                """
                SELECT count(*) AS failed_count
                FROM tenant.security_events
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                  AND event_type = 'login_failed'
                  AND occurred_at >= now() - make_interval(mins => :window_minutes)
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id, "window_minutes": window_minutes},
        ).mappings().one()
        return row["failed_count"]

    def lock_tenant_user(self, tenant_id: UUID, user_id: UUID) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.users SET status = 'locked', updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :user_id AND status <> 'locked'
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )

    def create_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        session_token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
        mfa_verified: bool,
    ) -> UUID:
        row = self._session.execute(
            text(
                """
                INSERT INTO tenant.user_sessions (
                  tenant_id, user_id, session_token_hash, ip_address, user_agent,
                  mfa_verified_at, expires_at
                )
                VALUES (
                  :tenant_id, :user_id, :session_token_hash, CAST(:ip_address AS inet), :user_agent,
                  CASE WHEN :mfa_verified THEN now() ELSE NULL END, :expires_at
                )
                RETURNING id
                """
            ),
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "session_token_hash": session_token_hash,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "mfa_verified": mfa_verified,
                "expires_at": expires_at,
            },
        ).one()
        return row.id

    def get_active_session_by_hash(self, session_token_hash: str) -> SessionRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT id, tenant_id, user_id, session_token_hash, expires_at, revoked_at
                FROM tenant.user_sessions
                WHERE session_token_hash = :session_token_hash
                LIMIT 1
                """
            ),
            {"session_token_hash": session_token_hash},
        ).mappings().one_or_none()
        return SessionRecord(**row) if row else None

    def rotate_session_token(self, session_id: UUID, session_token_hash: str, expires_at: datetime) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.user_sessions
                SET session_token_hash = :session_token_hash, expires_at = :expires_at
                WHERE id = :session_id AND revoked_at IS NULL
                """
            ),
            {"session_id": session_id, "session_token_hash": session_token_hash, "expires_at": expires_at},
        )

    def revoke_session(self, session_id: UUID) -> None:
        self._session.execute(
            text("UPDATE tenant.user_sessions SET revoked_at = COALESCE(revoked_at, now()) WHERE id = :session_id"),
            {"session_id": session_id},
        )

    def revoke_user_sessions(self, tenant_id: UUID, user_id: UUID, *, except_session_id: UUID | None = None) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.user_sessions
                SET revoked_at = COALESCE(revoked_at, now())
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND (CAST(:except_session_id AS uuid) IS NULL OR id <> CAST(:except_session_id AS uuid))
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id, "except_session_id": except_session_id},
        )

    def create_password_reset_token(
        self, *, tenant_id: UUID, user_id: UUID, token_hmac: str, expires_at: datetime
    ) -> None:
        self._revoke_pending_password_reset_tokens(tenant_id, user_id)
        self._session.execute(
            text(
                """
                INSERT INTO tenant.password_reset_tokens (tenant_id, user_id, token_hmac, expires_at)
                VALUES (:tenant_id, :user_id, :token_hmac, :expires_at)
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id, "token_hmac": token_hmac, "expires_at": expires_at},
        )

    def create_email_verification_token(
        self, *, tenant_id: UUID, user_id: UUID, email: str, token_hmac: str, expires_at: datetime
    ) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.email_verification_tokens
                SET status = 'revoked'
                WHERE tenant_id = :tenant_id AND user_id = :user_id AND status = 'pending'
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )
        self._session.execute(
            text(
                """
                INSERT INTO tenant.email_verification_tokens (tenant_id, user_id, email, token_hmac, expires_at)
                VALUES (:tenant_id, :user_id, :email, :token_hmac, :expires_at)
                """
            ),
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "email": email,
                "token_hmac": token_hmac,
                "expires_at": expires_at,
            },
        )

    def get_primary_totp_factor(self, tenant_id: UUID, user_id: UUID) -> MfaFactorRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT id, tenant_id, user_id, method::text AS method, secret_ref, is_primary, disabled_at
                FROM tenant.user_mfa_factors
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND method = 'totp'
                  AND is_primary
                  AND disabled_at IS NULL
                LIMIT 1
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        ).mappings().one_or_none()
        return MfaFactorRecord(**row) if row else None

    def create_pending_totp_factor(self, tenant_id: UUID, user_id: UUID, encrypted_secret: str) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.user_mfa_factors
                SET disabled_at = COALESCE(disabled_at, now())
                WHERE tenant_id = :tenant_id AND user_id = :user_id AND method = 'totp'
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )
        self._session.execute(
            text(
                """
                INSERT INTO tenant.user_mfa_factors (
                  tenant_id, user_id, method, secret_ref, is_primary, disabled_at
                )
                VALUES (:tenant_id, :user_id, 'totp', :secret_ref, true, now())
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id, "secret_ref": encrypted_secret},
        )

    def get_pending_totp_factor(self, tenant_id: UUID, user_id: UUID) -> MfaFactorRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT id, tenant_id, user_id, method::text AS method, secret_ref, is_primary, disabled_at
                FROM tenant.user_mfa_factors
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND method = 'totp'
                  AND is_primary
                  AND disabled_at IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        ).mappings().one_or_none()
        return MfaFactorRecord(**row) if row else None

    def enable_mfa_factor(self, factor_id: UUID) -> None:
        self._session.execute(
            text("UPDATE tenant.user_mfa_factors SET disabled_at = NULL WHERE id = :factor_id"),
            {"factor_id": factor_id},
        )

    def replace_recovery_codes(self, tenant_id: UUID, user_id: UUID, code_hashes: list[str]) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.user_mfa_factors
                SET disabled_at = COALESCE(disabled_at, now())
                WHERE tenant_id = :tenant_id AND user_id = :user_id AND method = 'recovery_code'
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )
        for code_hash in code_hashes:
            self._session.execute(
                text(
                    """
                    INSERT INTO tenant.user_mfa_factors (tenant_id, user_id, method, secret_ref, is_primary)
                    VALUES (:tenant_id, :user_id, 'recovery_code', :secret_ref, false)
                    """
                ),
                {"tenant_id": tenant_id, "user_id": user_id, "secret_ref": code_hash},
            )

    def consume_recovery_code(self, tenant_id: UUID, user_id: UUID, code_hash: str) -> bool:
        row = self._session.execute(
            text(
                """
                UPDATE tenant.user_mfa_factors
                SET disabled_at = now()
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND method = 'recovery_code'
                  AND secret_ref = :code_hash
                  AND disabled_at IS NULL
                RETURNING id
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id, "code_hash": code_hash},
        ).one_or_none()
        return row is not None

    def disable_mfa(self, tenant_id: UUID, user_id: UUID) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.user_mfa_factors
                SET disabled_at = COALESCE(disabled_at, now())
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )

    def write_security_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        event_type: str,
        outcome: str,
        request_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self._session.execute(
            text(
                """
                INSERT INTO tenant.security_events (
                  tenant_id, user_id, event_type, outcome, ip_address, user_agent, request_id, raw_event_snapshot
                )
                VALUES (
                  :tenant_id, :user_id, :event_type, :outcome, CAST(:ip_address AS inet),
                  :user_agent, :request_id, CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "event_type": event_type,
                "outcome": outcome,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id,
                "metadata": json.dumps(metadata or {}),
            },
        )

    def _revoke_pending_password_reset_tokens(self, tenant_id: UUID, user_id: UUID) -> None:
        self._session.execute(
            text(
                """
                UPDATE tenant.password_reset_tokens
                SET status = 'revoked'
                WHERE tenant_id = :tenant_id AND user_id = :user_id AND status = 'pending'
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )
