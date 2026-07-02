# Platform-Admin Identity

Tenant users and platform admins are separate identity classes, enforced structurally, not by
convention. This document explains why, and how the separation is implemented.

## Why tenant is not required on login

Tenant login is `{"email": "...", "password": "..."}` only. `tenant.users` has
`UNIQUE(tenant_id, email)`, not a global unique email, so the same email can legitimately exist
in more than one tenant (e.g. a contractor working with two client companies). Rather than push
tenant resolution onto the login screen (which would leak which tenants an email belongs to, and
add friction to the one common case where a login screen has no reasonable way to know the
tenant in advance), the Identity Service resolves the tenant internally:

1. Normalize the email (lowercase, trimmed -- `EmailModel.validate_email_shape`).
2. Query `tenant.users` **without** a `tenant_id` filter for active users matching that email
   (`TenantIdentityRepository.find_active_tenant_users_by_email`).
3. Exactly one match -> proceed with that tenant; set real tenant/RLS context
   (`set_pre_auth_tenant_context`) before any further tenant-scoped query.
4. Zero matches -> generic invalid-credentials response. No enumeration of which emails exist.
5. More than one match -> **do not guess.** Write an
   `identity.duplicate_active_email_conflict` event to `platform.audit_logs` (see
   [docs/security/auth-audit-events.md](auth-audit-events.md)) and return the same generic
   invalid-credentials response. This is a configuration/security anomaly (the same email
   should not normally be active in more than one tenant unless that is an intentional
   multi-tenant arrangement the schema doesn't yet disambiguate), surfaced for operators to
   investigate rather than silently resolved by picking a tenant at random.

Password reset and email verification tokens have the identical structural problem
(`tenant.password_reset_tokens`/`tenant.email_verification_tokens` are also
`UNIQUE(tenant_id, token_hmac)`, not globally unique), so the same tenant-less token contract
applies: the reset/verify link never carries a tenant, and consumption resolves the tenant from
the token itself (`consume_password_reset_token_global` / `consume_email_verification_token_global`).

### How the cross-tenant lookup is RLS-safe

`tenant.users` (and its token tables) are RLS-forced:
`USING (tenant_id = app.current_tenant_id() OR app.is_platform_admin())`. Before the tenant is
known, neither GUC is set to a real value, so a naive query would return zero rows regardless of
what exists. The repository sets `app.is_platform_admin = true` as a **transaction-local**
`set_config(..., true)` immediately before the one lookup query
(`TenantIdentityRepository.set_cross_tenant_lookup_guc`), then immediately supersedes it with
real tenant-scoped context (`set_pre_auth_tenant_context`) once a single tenant is resolved, or
lets the request end (its session/connection is closed and never reused --
`gnxthire_common.db.session_scope` opens one session per request). This is intentionally
**not** the same code path as `set_platform_admin_context` in `packages/backend-common` (which
represents a real, authenticated platform admin acting in their own context) -- this is a narrow,
anonymous, pre-authentication system bypass, fully contained inside
`gnxthire_identity.tenant.repository` and never exposed outside it.

## Platform-admin separation

- **Separate tables.** Platform-admin credentials/sessions/MFA/reset-tokens live in
  `platform.platform_users`, `platform.platform_user_sessions`,
  `platform.platform_user_mfa_factors`, `platform.platform_password_reset_tokens`,
  `platform.platform_email_verification_tokens` -- never in the `tenant.*` tables. Login queries
  only one table set per realm; a tenant user's email is never visible to platform-admin login,
  and vice versa.
- **Separate tokens.** See
  [docs/security/token-session-strategy.md](token-session-strategy.md). Platform-admin access
  tokens carry no `tid` claim and a different audience
  (`IDENTITY_PLATFORM_ADMIN_AUDIENCE`), so a tenant token can never pass
  `authenticated_platform_admin`'s verification, and a platform-admin token can never pass
  `authenticated_tenant_user`'s -- rejected at signature verification, before any database
  lookup.
- **No tenant/RLS context from platform-admin auth.** `platform.*` tables carry no `tenant_id`
  column and are therefore never subject to the tenant-RLS auto-enable loop
  (`db/schema/11_rls_policies.sql` only targets tables that have a `tenant_id` column).
  `authenticated_platform_admin` calls `set_platform_admin_context`, which never sets
  `app.current_tenant_id`. Access control for platform tables is enforced entirely at the
  application layer (route dependency + coarse-grained "is an active platform admin" check).
- **Simpler resolution.** `platform.platform_users.email` has a real
  `UNIQUE` constraint (globally unique, not per-tenant), so platform-admin login has no
  cross-realm ambiguity to resolve at all -- it is a direct, single lookup.
- **Separate audit trail.** See
  [docs/security/auth-audit-events.md](auth-audit-events.md) -- distinguishable `actor_type`
  and `platform_admin.*`-prefixed action keys.
- **No RBAC decisions in this phase.** Platform-admin user-management routes
  (`/v1/identity/platform-users/*`) are gated on "authenticated, active platform admin" only.
  Fine-grained permission checks are explicitly out of Phase 2 scope; adding them here would
  violate the phase boundary, not strengthen security.

## Ownership boundary with the future Platform Admin Service

Per the service-to-table ownership matrix, Identity owns platform-admin **users** (auth,
sessions, MFA, credential lifecycle). The Platform Admin Service (a later phase) owns tenant
lifecycle, plans, quotas, features, support sessions, and platform-wide governance -- it does
not own platform-admin login credentials. `/v1/identity/platform-users/*` is therefore
implemented here, not deferred.

## Bootstrapping the first platform admin

There is intentionally no self-registration HTTP route for platform admins (an HTTP "become the
first admin" endpoint would be a standing security hole). Use the out-of-band CLI:

```powershell
python scripts/bootstrap_platform_admin.py --email admin@gnxthire.com --password "..." --display-name "Ops Admin"
```

It refuses to run outside local/test `APP_ENV` unless `--i-understand-this-is-not-for-production`
is passed, and enforces the same password policy as every other password-set path.

## Known limitation: `mfa_required` does not yet block login

See [docs/security/mfa.md](mfa.md) -- the flag is real, persisted, and audited, but does not
currently gate login for an admin who has not yet completed TOTP setup (a chicken-and-egg problem
requiring a step-up token type that is out of Phase 2 scope). This is documented, not silently
missing.
