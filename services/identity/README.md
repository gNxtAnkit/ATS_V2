# Identity Service

Identity Service code lives in `services/identity/src/gnxthire_identity`. It implements two
strictly separate identity classes: tenant users and platform admins. See
[docs/security/platform-admin-identity.md](../../docs/security/platform-admin-identity.md) for
the full separation rationale.

## Tenant-user identity (`gnxthire_identity.tenant`)

- Login is email + password only (`POST /v1/identity/auth/login`). The tenant is never
  supplied by the caller; it is resolved internally from the normalized email against
  `tenant.users` (see the tenant-resolution rule below).
- Logout, refresh (rotating), and `me` route handlers.
- Forgot/reset password flow with SMTP email delivery and single-use HMAC-stored tokens.
- Email verification flow with SMTP email delivery and single-use HMAC-stored tokens.
- Password change (requires current password, revokes other sessions).
- TOTP MFA setup, confirmation, challenge verification, recovery-code regeneration, and disable.
  Setup is separate from enabled state; login never returns normal tokens before MFA
  verification when an active factor exists.
- Refresh token persistence/rotation through `tenant.user_sessions`.
- Tenant security event writes through `tenant.security_events`.
- Failed-login tracking and automatic account lockout (see `IDENTITY_LOGIN_LOCKOUT_*` settings).
- Rate-limit adapters for Redis and local/test memory.

**Tenant resolution rule**: `tenant.users` has `UNIQUE(tenant_id, email)`, not a global unique
email. Login/forgot-password/reset/verify all resolve the tenant by querying across tenants for
the normalized email. If zero active users match, the caller gets a generic invalid-credentials
response (no enumeration). If more than one active user matches the same email across different
tenants, the service does not guess: it fails the request generically and writes an
`identity.duplicate_active_email_conflict` event to `platform.audit_logs` for operators to
investigate. See `TenantIdentityRepository.find_active_tenant_users_by_email` /
`find_tenant_users_by_email`.

## Platform-admin identity (`gnxthire_identity.platform_admin`)

- Login is email + password only (`POST /v1/identity/platform-admin/auth/login`), against
  `platform.platform_users` exclusively. `platform.platform_users.email` is globally unique, so
  there is no cross-tenant ambiguity to resolve.
- Logout, refresh (rotating), `me`, forgot/reset password, email verification, password change.
- TOTP MFA setup/confirm/verify/recovery-codes/disable, mirroring the tenant flow against
  `platform.platform_user_mfa_factors`.
- Platform-admin tokens never carry a `tenant_id` claim and use a distinct audience
  (`IDENTITY_PLATFORM_ADMIN_AUDIENCE`). Platform-admin authentication never sets tenant/RLS
  context (`app.current_tenant_id` is never touched by the platform-admin auth path).
- Identity-owned platform-admin user lifecycle management:
  `GET/POST /v1/identity/platform-users`, `.../{id}`, `.../activate`, `.../deactivate`,
  `.../lock`, `.../unlock`, `.../require-password-reset`, `.../require-mfa`. Gated by
  "authenticated, active platform admin" only -- fine-grained RBAC is out of Phase 2 scope.
- Failed-login tracking and automatic account lockout
  (`IDENTITY_PLATFORM_ADMIN_LOGIN_LOCKOUT_*` settings), counted from `platform.audit_logs`.
- There is no self-registration route for platform admins by design. Bootstrap or recover the
  first platform admin's password with `scripts/bootstrap_platform_admin.py` (out-of-band CLI,
  refuses to run outside local/test `APP_ENV` without an explicit override flag).

## Shared, realm-agnostic modules

`security.py` (hashing, signed tokens, TOTP, opaque-token HMAC, secret encryption), `email.py`
(SMTP adapter), `rate_limit.py` (Redis/memory adapters), `config.py` (settings), and
`schemas.py` (DTOs shared by both realms) are used by both `tenant/` and `platform_admin/`
without duplication.

## Running locally

```powershell
python -m uvicorn gnxthire_identity.main:app --reload --port 8001
```

Mailpit/Mailhog local SMTP defaults are in `.env.example`. For Gmail on port 587 use
`SMTP_USE_TLS=true` and `SMTP_USE_SSL=false`; implicit SSL is for port 465-style SMTP only.

## Documentation

- [docs/api/identity-api.md](../../docs/api/identity-api.md) -- full endpoint list
- [docs/security/platform-admin-identity.md](../../docs/security/platform-admin-identity.md) --
  tenant/platform-admin separation
- [docs/security/token-session-strategy.md](../../docs/security/token-session-strategy.md)
- [docs/security/mfa.md](../../docs/security/mfa.md)
- [docs/security/email-verification-and-password-reset.md](../../docs/security/email-verification-and-password-reset.md)
- [docs/security/auth-audit-events.md](../../docs/security/auth-audit-events.md)
- [docs/runbooks/identity-email-delivery.md](../../docs/runbooks/identity-email-delivery.md)


admin@gnxthire.com (platform admin, password SuperStrongPass123!) — created via scripts/bootstrap_platform_admin.py during smoke testing.
