"""Add platform-admin authentication schema (password, sessions, MFA, reset/verify tokens).

Revision ID: 0002_platform_admin_identity
Revises: 0001_initial
Create Date: 2026-07-01

Identity Service Phase 2 correction: platform.platform_users previously had no
password_hash/session/MFA/reset-token storage, so platform-admin authentication
could not be implemented. This migration is additive only.

Important: this migration intentionally does NOT call `Base.metadata.create_all()`
(that is 0001's job). Every statement below is written with IF NOT EXISTS / guarded
DO blocks so it is safe to run both against:
  - an existing database that already ran the old 0001 (needs these objects created), and
  - a brand-new database bootstrapped from the *current* db/models/* (0001 will already
    have created these exact tables/columns/enum value via Base.metadata.create_all,
    since db/models/core.py and db/models/platform.py were updated alongside this
    migration) — in that case every statement here safely no-ops.

The platform schema has no tenant_id column on these tables and is therefore never
subject to the tenant RLS auto-enable loop in 0001 (db/schema/11_rls_policies.sql /
RLS_POLICIES_SQL only targets tables with a tenant_id column). Access control for
platform-admin tables is enforced entirely at the application layer.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "0002_platform_admin_identity"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ADD_LOCKED_STATUS_SQL = "ALTER TYPE platform_user_status_enum ADD VALUE IF NOT EXISTS 'locked'"

ADD_PLATFORM_USER_COLUMNS_SQL = """
ALTER TABLE platform.platform_users ADD COLUMN IF NOT EXISTS password_hash text;
ALTER TABLE platform.platform_users ADD COLUMN IF NOT EXISTS email_verified_at timestamptz;
ALTER TABLE platform.platform_users ADD COLUMN IF NOT EXISTS mfa_required boolean NOT NULL DEFAULT false;
"""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS platform.platform_user_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  session_token_hash text NOT NULL,
  ip_address inet,
  user_agent text,
  mfa_verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  CONSTRAINT uq_platform_user_sessions_token_hash UNIQUE (session_token_hash),
  CONSTRAINT fk_platform_user_sessions_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_platform_user_sessions_expires_after_created CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS platform.platform_password_reset_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  token_hmac text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','used','expired','revoked')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_platform_password_reset_tokens_hmac UNIQUE (token_hmac),
  CONSTRAINT fk_platform_password_reset_tokens_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_platform_password_reset_tokens_expires_after_requested CHECK (expires_at > requested_at)
);

CREATE TABLE IF NOT EXISTS platform.platform_email_verification_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  token_hmac text NOT NULL,
  email citext NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','used','expired','revoked')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_platform_email_verification_tokens_hmac UNIQUE (token_hmac),
  CONSTRAINT fk_platform_email_verification_tokens_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_platform_email_verification_tokens_expires_after_requested CHECK (expires_at > requested_at)
);

CREATE TABLE IF NOT EXISTS platform.platform_user_mfa_factors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  method mfa_method_enum NOT NULL,
  secret_ref text,
  phone_e164 text,
  is_primary boolean NOT NULL DEFAULT false,
  enabled_at timestamptz NOT NULL DEFAULT now(),
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_platform_user_mfa_factors_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id)
);
"""

CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS ix_platform_user_sessions_platform_user_id ON platform.platform_user_sessions(platform_user_id);
CREATE INDEX IF NOT EXISTS ix_platform_password_reset_tokens_platform_user_id ON platform.platform_password_reset_tokens(platform_user_id);
CREATE INDEX IF NOT EXISTS ix_platform_email_verification_tokens_platform_user_id ON platform.platform_email_verification_tokens(platform_user_id);
CREATE INDEX IF NOT EXISTS ix_platform_user_mfa_factors_platform_user_id ON platform.platform_user_mfa_factors(platform_user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_platform_password_reset_tokens_one_active
  ON platform.platform_password_reset_tokens(platform_user_id) WHERE status = 'pending';
CREATE UNIQUE INDEX IF NOT EXISTS uq_platform_user_mfa_factors_primary
  ON platform.platform_user_mfa_factors(platform_user_id) WHERE is_primary AND disabled_at IS NULL;
"""

def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(ADD_LOCKED_STATUS_SQL)
    op.execute(ADD_PLATFORM_USER_COLUMNS_SQL)
    op.execute(CREATE_TABLES_SQL)
    op.execute(CREATE_INDEXES_SQL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS platform.platform_user_mfa_factors CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.platform_email_verification_tokens CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.platform_password_reset_tokens CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.platform_user_sessions CASCADE")
    op.execute("ALTER TABLE platform.platform_users DROP COLUMN IF EXISTS mfa_required")
    op.execute("ALTER TABLE platform.platform_users DROP COLUMN IF EXISTS email_verified_at")
    op.execute("ALTER TABLE platform.platform_users DROP COLUMN IF EXISTS password_hash")
    # The 'locked' enum value added to platform_user_status_enum is intentionally NOT
    # removed here: PostgreSQL cannot drop a single enum value without recreating the
    # type, which is unsafe for local/dev rollback and out of scope for production
    # rollback (restore from backup per repo convention, see 0001's downgrade docstring).
