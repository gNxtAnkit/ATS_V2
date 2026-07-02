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
