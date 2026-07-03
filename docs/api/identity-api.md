# Identity API

Two realm-separated base paths. A token issued for one realm is always rejected by the other
(different signing audience; see
[docs/security/token-session-strategy.md](../security/token-session-strategy.md)).

## Tenant-user endpoints -- base path `/v1/identity`

Login body is `{"email": "...", "password": "..."}` only. Tenant is never supplied by the
caller; it is resolved internally from the normalized email (see
[docs/security/platform-admin-identity.md](../security/platform-admin-identity.md) for the
resolution/duplicate-handling rule).

- `POST /auth/login`
- `GET /auth/password-policy`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/request-email-verification`
- `POST /auth/verify-email`
- `POST /auth/change-password`
- `POST /mfa/totp/setup`
- `POST /mfa/totp/confirm`
- `POST /mfa/totp/verify`
- `POST /mfa/recovery-code/verify`
- `POST /mfa/recovery-codes/regenerate`
- `POST /mfa/disable`

### MFA login responses

Password-only login with no active MFA factor returns `status="authenticated"` and a normal
`tokens` object.

Password login with active MFA returns no normal tokens:

```json
{
  "status": "mfa_required",
  "mfa_required": true,
  "mfa_challenge_token": "short-lived-token",
  "challenge_token": "short-lived-token",
  "available_methods": ["totp", "recovery_code"],
  "expires_in_seconds": 300,
  "tokens": null
}
```

Successful `/mfa/totp/verify` or `/mfa/recovery-code/verify` returns the normal authenticated
login response with access and refresh tokens. Challenge tokens are not access tokens and are
rejected by `/auth/me` and other authenticated APIs.

`GET /auth/me` includes MFA state for the frontend:

```json
{
  "actor_id": "...",
  "actor_type": "tenant_user",
  "tenant_id": "...",
  "email": "user@example.com",
  "display_name": "User",
  "email_verified": true,
  "mfa_enabled": true,
  "mfa_methods": ["totp"],
  "pending_mfa_setup": false,
  "recovery_codes_remaining": 8
}
```

`POST /mfa/recovery-codes/regenerate` and `POST /mfa/disable` require the current password.
Setup returns a conflict when MFA is already enabled; disable and recovery-code regeneration
return a conflict when MFA is not enabled.

## Platform-admin endpoints -- base path `/v1/identity/platform-admin`

Login body is `{"email": "...", "password": "..."}` only, checked against
`platform.platform_users` exclusively (never `tenant.users`). Platform-admin authentication
never sets tenant/RLS context.

- `POST /auth/login`
- `GET /auth/password-policy`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/request-email-verification`
- `POST /auth/verify-email`
- `POST /auth/change-password`
- `POST /mfa/totp/setup`
- `POST /mfa/totp/confirm`
- `POST /mfa/totp/verify`
- `POST /mfa/recovery-code/verify`
- `POST /mfa/recovery-codes/regenerate`
- `POST /mfa/disable`

## Platform-admin user management -- base path `/v1/identity/platform-users`

Identity-owned platform-admin credential/status lifecycle only (not tenant management, billing,
or support tooling -- those belong to the future Platform Admin Service). Requires an
authenticated, active platform admin; fine-grained RBAC is out of Phase 2 scope.

- `GET /` (cursor-paginated)
- `POST /`
- `GET /{platform_admin_user_id}`
- `PATCH /{platform_admin_user_id}`
- `POST /{platform_admin_user_id}/activate`
- `POST /{platform_admin_user_id}/deactivate`
- `POST /{platform_admin_user_id}/lock`
- `POST /{platform_admin_user_id}/unlock`
- `POST /{platform_admin_user_id}/require-password-reset`
- `POST /{platform_admin_user_id}/require-mfa`

## Errors

All errors use:

```json
{
  "error": {
    "code": "authentication_required",
    "message": "Authentication required",
    "field_errors": [],
    "request_id": "req_123"
  }
}
```

Login, forgot-password, and email-verification-request responses are enumeration-safe: unknown
emails, wrong passwords, and (for tenant login) duplicate-active-email conflicts all return the
same generic message.
