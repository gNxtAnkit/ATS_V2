# Auth Audit Events

## Tenant users

Tenant identity writes security events to `tenant.security_events` (append-only; a database
trigger denies `UPDATE`/`DELETE`). Events include request id, tenant id, user id when known,
event type, outcome, IP address, user agent, and safe metadata only.

Event types include `login_success`, `login_failed`, `account_locked`, `logout`,
`password_reset_requested`, `password_reset_completed`, `password_changed`,
`email_verification_requested`, `email_verified`, `mfa_enabled`, `mfa_disabled`, `mfa_failed`.

## Platform admins

Platform-admin identity writes security/audit events to `platform.audit_logs` (append-only;
same deny-update-delete trigger), not to a separate `platform.security_events` table -- there is
no such table, and `platform.audit_logs` already has everything needed (`ip_address`,
`user_agent`, `request_id`, immutable `after_state` jsonb snapshot) plus an `actor_type` that
already distinguishes `platform_user` (self-service actions) from `system` (anonymous/failed
pre-auth attempts). Action keys are prefixed `platform_admin.*`
(`platform_admin.login_success`, `platform_admin.login_failed`, `platform_admin.account_locked`,
`platform_admin.password_reset_completed`, `platform_admin.mfa_enabled`,
`platform_admin.user_status_changed`, etc.) so tenant and platform-admin events are
unambiguously distinguishable even though they can share the same sink table.

## Cross-tenant safety event

When a tenant-user login/forgot-password/verification-request resolves more than one active
user for the same normalized email across different tenants, the service does not pick one at
random. It writes `identity.duplicate_active_email_conflict` to `platform.audit_logs`
(`tenant_id = NULL`, since the conflict spans tenants and cannot be attributed to one) with the
matching tenant ids in `after_state`, then returns the same generic error the caller would get
for an unknown email.

## Rules

Never store raw passwords, raw reset or verification tokens, full JWTs, TOTP secrets, or
recovery codes in security/audit event metadata.

`gnxthire_common.db.session_scope()` commits on a handled `AppError` (not just on success), so
these events persist even when the request that triggered them ends in a 401/429/etc. response
-- see [docs/engineering/backend-common-foundation.md](../engineering/backend-common-foundation.md).
