from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

PENDING_TOTP_SECRET_PREFIX = "pending:"


@dataclass(frozen=True)
class PlatformUserRecord:
    id: UUID
    email: str
    display_name: str
    status: str
    password_hash: str | None
    email_verified_at: datetime | None
    mfa_required: bool
    last_login_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class PlatformSessionRecord:
    id: UUID
    platform_user_id: UUID
    session_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True)
class PlatformMfaFactorRecord:
    id: UUID
    platform_user_id: UUID
    method: str
    secret_ref: str | None
    is_primary: bool
    disabled_at: datetime | None


_USER_COLUMNS = """
    id, email::text AS email, display_name, status::text AS status, password_hash,
    email_verified_at, mfa_required, last_login_at, created_at
"""


class PlatformAdminRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # -- Auth ------------------------------------------------------------------------
    # No RLS applies to the platform schema, so unlike tenant.users these lookups need
    # no pre-auth context bypass at all: platform.platform_users.email is globally
    # unique, so login/reset/verify are simple direct queries.

    def get_platform_user_by_email(self, email: str) -> PlatformUserRecord | None:
        row = self._session.execute(
            text(
                f"""
                SELECT {_USER_COLUMNS}
                FROM platform.platform_users
                WHERE email = :email AND deleted_at IS NULL
                LIMIT 1
                """
            ),
            {"email": email},
        ).mappings().one_or_none()
        return PlatformUserRecord(**row) if row else None

    def get_platform_user_by_id(self, user_id: UUID) -> PlatformUserRecord | None:
        row = self._session.execute(
            text(
                f"""
                SELECT {_USER_COLUMNS}
                FROM platform.platform_users
                WHERE id = :user_id AND deleted_at IS NULL
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).mappings().one_or_none()
        return PlatformUserRecord(**row) if row else None

    def update_last_login(self, user_id: UUID) -> None:
        self._session.execute(
            text("UPDATE platform.platform_users SET last_login_at = now() WHERE id = :user_id"),
            {"user_id": user_id},
        )

    def update_password(self, user_id: UUID, password_hash: str) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_users SET password_hash = :password_hash, updated_at = now() WHERE id = :user_id"
            ),
            {"user_id": user_id, "password_hash": password_hash},
        )

    def mark_email_verified(self, user_id: UUID) -> None:
        self._session.execute(
            text(
                """
                UPDATE platform.platform_users
                SET email_verified_at = COALESCE(email_verified_at, now()), updated_at = now()
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )

    def count_recent_failed_logins(self, platform_user_id: UUID, *, window_minutes: int) -> int:
        row = self._session.execute(
            text(
                """
                SELECT count(*) AS failed_count
                FROM platform.audit_logs
                WHERE actor_type IN ('platform_user', 'system')
                  AND object_schema = 'platform' AND object_table = 'platform_users'
                  AND object_id = :platform_user_id
                  AND action_key = 'platform_admin.login_failed'
                  AND occurred_at >= now() - make_interval(mins => :window_minutes)
                """
            ),
            {"platform_user_id": platform_user_id, "window_minutes": window_minutes},
        ).mappings().one()
        return row["failed_count"]

    def lock_platform_user(self, platform_user_id: UUID) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_users SET status = 'locked', updated_at = now() WHERE id = :id AND status <> 'locked'"
            ),
            {"id": platform_user_id},
        )

    def set_platform_user_status(self, platform_user_id: UUID, status: str) -> None:
        self._session.execute(
            text("UPDATE platform.platform_users SET status = :status, updated_at = now() WHERE id = :id"),
            {"id": platform_user_id, "status": status},
        )

    def set_mfa_required(self, platform_user_id: UUID, mfa_required: bool) -> None:
        self._session.execute(
            text("UPDATE platform.platform_users SET mfa_required = :mfa_required, updated_at = now() WHERE id = :id"),
            {"id": platform_user_id, "mfa_required": mfa_required},
        )

    def update_display_name(self, platform_user_id: UUID, display_name: str) -> None:
        self._session.execute(
            text("UPDATE platform.platform_users SET display_name = :display_name, updated_at = now() WHERE id = :id"),
            {"id": platform_user_id, "display_name": display_name},
        )

    def create_platform_user(self, *, email: str, display_name: str) -> PlatformUserRecord:
        row = self._session.execute(
            text(
                f"""
                INSERT INTO platform.platform_users (email, display_name, status)
                VALUES (:email, :display_name, 'invited')
                RETURNING {_USER_COLUMNS}
                """
            ),
            {"email": email, "display_name": display_name},
        ).mappings().one()
        return PlatformUserRecord(**row)

    def list_platform_users(
        self, *, after_created_at: datetime | None, after_id: UUID | None, limit: int
    ) -> list[PlatformUserRecord]:
        rows = self._session.execute(
            text(
                f"""
                SELECT {_USER_COLUMNS}
                FROM platform.platform_users
                WHERE deleted_at IS NULL
                  AND (
                    CAST(:after_created_at AS timestamptz) IS NULL
                    OR (created_at, id) > (CAST(:after_created_at AS timestamptz), CAST(:after_id AS uuid))
                  )
                ORDER BY created_at, id
                LIMIT :limit
                """
            ),
            {"after_created_at": after_created_at, "after_id": after_id, "limit": limit},
        ).mappings().all()
        return [PlatformUserRecord(**row) for row in rows]

    # -- Sessions ----------------------------------------------------------------------

    def create_session(
        self,
        *,
        platform_user_id: UUID,
        session_token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
        mfa_verified: bool,
    ) -> UUID:
        row = self._session.execute(
            text(
                """
                INSERT INTO platform.platform_user_sessions (
                  platform_user_id, session_token_hash, ip_address, user_agent, mfa_verified_at, expires_at
                )
                VALUES (
                  :platform_user_id, :session_token_hash, CAST(:ip_address AS inet), :user_agent,
                  CASE WHEN :mfa_verified THEN now() ELSE NULL END, :expires_at
                )
                RETURNING id
                """
            ),
            {
                "platform_user_id": platform_user_id,
                "session_token_hash": session_token_hash,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "mfa_verified": mfa_verified,
                "expires_at": expires_at,
            },
        ).one()
        return row.id

    def get_active_session_by_hash(self, session_token_hash: str) -> PlatformSessionRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT id, platform_user_id, session_token_hash, expires_at, revoked_at
                FROM platform.platform_user_sessions
                WHERE session_token_hash = :session_token_hash
                LIMIT 1
                """
            ),
            {"session_token_hash": session_token_hash},
        ).mappings().one_or_none()
        return PlatformSessionRecord(**row) if row else None

    def rotate_session_token(self, session_id: UUID, session_token_hash: str, expires_at: datetime) -> None:
        self._session.execute(
            text(
                """
                UPDATE platform.platform_user_sessions
                SET session_token_hash = :session_token_hash, expires_at = :expires_at
                WHERE id = :session_id AND revoked_at IS NULL
                """
            ),
            {"session_id": session_id, "session_token_hash": session_token_hash, "expires_at": expires_at},
        )

    def revoke_session(self, session_id: UUID) -> None:
        self._session.execute(
            text("UPDATE platform.platform_user_sessions SET revoked_at = COALESCE(revoked_at, now()) WHERE id = :session_id"),
            {"session_id": session_id},
        )

    def revoke_user_sessions(self, platform_user_id: UUID, *, except_session_id: UUID | None = None) -> None:
        self._session.execute(
            text(
                """
                UPDATE platform.platform_user_sessions
                SET revoked_at = COALESCE(revoked_at, now())
                WHERE platform_user_id = :platform_user_id
                  AND (CAST(:except_session_id AS uuid) IS NULL OR id <> CAST(:except_session_id AS uuid))
                """
            ),
            {"platform_user_id": platform_user_id, "except_session_id": except_session_id},
        )

    # -- Password reset / email verification tokens -------------------------------------

    def create_password_reset_token(self, *, platform_user_id: UUID, token_hmac: str, expires_at: datetime) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_password_reset_tokens SET status = 'revoked' WHERE platform_user_id = :id AND status = 'pending'"
            ),
            {"id": platform_user_id},
        )
        self._session.execute(
            text(
                """
                INSERT INTO platform.platform_password_reset_tokens (platform_user_id, token_hmac, expires_at)
                VALUES (:platform_user_id, :token_hmac, :expires_at)
                """
            ),
            {"platform_user_id": platform_user_id, "token_hmac": token_hmac, "expires_at": expires_at},
        )

    def revoke_pending_password_reset_tokens(self, platform_user_id: UUID) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_password_reset_tokens SET status = 'revoked' WHERE platform_user_id = :id AND status = 'pending'"
            ),
            {"id": platform_user_id},
        )

    def consume_password_reset_token(self, token_hmac: str) -> UUID | None:
        row = self._session.execute(
            text(
                """
                UPDATE platform.platform_password_reset_tokens
                SET status = 'used', used_at = now()
                WHERE token_hmac = :token_hmac AND status = 'pending' AND expires_at > now()
                RETURNING platform_user_id
                """
            ),
            {"token_hmac": token_hmac},
        ).one_or_none()
        return row.platform_user_id if row else None

    def create_email_verification_token(
        self, *, platform_user_id: UUID, email: str, token_hmac: str, expires_at: datetime
    ) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_email_verification_tokens SET status = 'revoked' WHERE platform_user_id = :id AND status = 'pending'"
            ),
            {"id": platform_user_id},
        )
        self._session.execute(
            text(
                """
                INSERT INTO platform.platform_email_verification_tokens (platform_user_id, email, token_hmac, expires_at)
                VALUES (:platform_user_id, :email, :token_hmac, :expires_at)
                """
            ),
            {"platform_user_id": platform_user_id, "email": email, "token_hmac": token_hmac, "expires_at": expires_at},
        )

    def consume_email_verification_token(self, token_hmac: str) -> UUID | None:
        row = self._session.execute(
            text(
                """
                UPDATE platform.platform_email_verification_tokens
                SET status = 'used', used_at = now()
                WHERE token_hmac = :token_hmac AND status = 'pending' AND expires_at > now()
                RETURNING platform_user_id
                """
            ),
            {"token_hmac": token_hmac},
        ).one_or_none()
        return row.platform_user_id if row else None

    # -- MFA -----------------------------------------------------------------------------

    def get_primary_totp_factor(self, platform_user_id: UUID) -> PlatformMfaFactorRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT id, platform_user_id, method::text AS method, secret_ref, is_primary, disabled_at
                FROM platform.platform_user_mfa_factors
                WHERE platform_user_id = :platform_user_id
                  AND method = 'totp' AND is_primary AND disabled_at IS NULL
                LIMIT 1
                """
            ),
            {"platform_user_id": platform_user_id},
        ).mappings().one_or_none()
        return PlatformMfaFactorRecord(**row) if row else None

    def create_pending_totp_factor(self, platform_user_id: UUID, encrypted_secret: str) -> None:
        self._session.execute(
            text(
                """
                UPDATE platform.platform_user_mfa_factors
                SET disabled_at = COALESCE(disabled_at, now())
                WHERE platform_user_id = :id
                  AND method = 'totp'
                  AND secret_ref LIKE 'pending:%'
                """
            ),
            {"id": platform_user_id},
        )
        self._session.execute(
            text(
                """
                INSERT INTO platform.platform_user_mfa_factors (platform_user_id, method, secret_ref, is_primary, disabled_at)
                VALUES (:platform_user_id, 'totp', :secret_ref, true, now())
                """
            ),
            {"platform_user_id": platform_user_id, "secret_ref": f"{PENDING_TOTP_SECRET_PREFIX}{encrypted_secret}"},
        )

    def get_pending_totp_factor(self, platform_user_id: UUID) -> PlatformMfaFactorRecord | None:
        row = self._session.execute(
            text(
                """
                SELECT id, platform_user_id, method::text AS method, secret_ref, is_primary, disabled_at
                FROM platform.platform_user_mfa_factors
                WHERE platform_user_id = :platform_user_id
                  AND method = 'totp' AND is_primary AND disabled_at IS NOT NULL
                  AND secret_ref LIKE 'pending:%'
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"platform_user_id": platform_user_id},
        ).mappings().one_or_none()
        return PlatformMfaFactorRecord(**row) if row else None

    def enable_mfa_factor(self, factor_id: UUID, encrypted_secret: str) -> None:
        self._session.execute(
            text(
                """
                UPDATE platform.platform_user_mfa_factors
                SET disabled_at = NULL, secret_ref = :secret_ref
                WHERE id = :factor_id
                """
            ),
            {"factor_id": factor_id, "secret_ref": encrypted_secret},
        )

    def replace_recovery_codes(self, platform_user_id: UUID, code_hashes: list[str]) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_user_mfa_factors SET disabled_at = COALESCE(disabled_at, now()) WHERE platform_user_id = :id AND method = 'recovery_code'"
            ),
            {"id": platform_user_id},
        )
        for code_hash in code_hashes:
            self._session.execute(
                text(
                    """
                    INSERT INTO platform.platform_user_mfa_factors (platform_user_id, method, secret_ref, is_primary)
                    VALUES (:platform_user_id, 'recovery_code', :secret_ref, false)
                    """
                ),
                {"platform_user_id": platform_user_id, "secret_ref": code_hash},
            )

    def consume_recovery_code(self, platform_user_id: UUID, code_hash: str) -> bool:
        row = self._session.execute(
            text(
                """
                UPDATE platform.platform_user_mfa_factors
                SET disabled_at = now()
                WHERE platform_user_id = :platform_user_id
                  AND method = 'recovery_code' AND secret_ref = :code_hash AND disabled_at IS NULL
                RETURNING id
                """
            ),
            {"platform_user_id": platform_user_id, "code_hash": code_hash},
        ).one_or_none()
        return row is not None

    def count_active_recovery_codes(self, platform_user_id: UUID) -> int:
        row = self._session.execute(
            text(
                """
                SELECT count(*) AS remaining
                FROM platform.platform_user_mfa_factors
                WHERE platform_user_id = :platform_user_id
                  AND method = 'recovery_code'
                  AND disabled_at IS NULL
                """
            ),
            {"platform_user_id": platform_user_id},
        ).mappings().one()
        return row["remaining"]

    def disable_mfa(self, platform_user_id: UUID) -> None:
        self._session.execute(
            text(
                "UPDATE platform.platform_user_mfa_factors SET disabled_at = COALESCE(disabled_at, now()) WHERE platform_user_id = :id"
            ),
            {"id": platform_user_id},
        )

    def has_active_mfa_factor(self, platform_user_id: UUID) -> bool:
        row = self._session.execute(
            text(
                """
                SELECT 1 FROM platform.platform_user_mfa_factors
                WHERE platform_user_id = :platform_user_id AND method = 'totp' AND is_primary AND disabled_at IS NULL
                LIMIT 1
                """
            ),
            {"platform_user_id": platform_user_id},
        ).one_or_none()
        return row is not None

    # -- Audit -----------------------------------------------------------------------------

    def write_audit_log(
        self,
        *,
        actor_type: str,
        actor_platform_user_id: UUID | None,
        action_key: str,
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
                  tenant_id, actor_type, actor_platform_user_id, action_key,
                  object_schema, object_table, object_id, after_state, ip_address, user_agent, request_id
                ) VALUES (
                  NULL, :actor_type, :actor_platform_user_id, :action_key,
                  'platform', 'platform_users', :object_id, CAST(:after_state AS jsonb),
                  CAST(:ip_address AS inet), :user_agent, :request_id
                )
                """
            ),
            {
                "actor_type": actor_type,
                "actor_platform_user_id": actor_platform_user_id,
                "action_key": action_key,
                "object_id": object_id,
                "after_state": json.dumps(after_state or {}),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id,
            },
        )
