# Token and Session Strategy

- Access and refresh tokens are short-lived/rotating signed HS256 tokens with a unique `jti`
  per issuance (guarantees two tokens for the same session are never byte-identical, even if
  issued within the same second).
- Tenant tokens carry `actor_type=tenant_user`, a `tid` (tenant id) claim, and
  `aud=IDENTITY_TENANT_AUDIENCE`. Refresh tokens are persisted only as HMACs in
  `tenant.user_sessions.session_token_hash`.
- Platform-admin tokens carry `actor_type=platform_user`, **no** `tid` claim, and
  `aud=IDENTITY_PLATFORM_ADMIN_AUDIENCE`. Refresh tokens are persisted only as HMACs in
  `platform.platform_user_sessions.session_token_hash`.
- Because each realm's auth dependency verifies against its own audience
  (`authenticated_tenant_user` requires `IDENTITY_TENANT_AUDIENCE`,
  `authenticated_platform_admin` requires `IDENTITY_PLATFORM_ADMIN_AUDIENCE`), a token from one
  realm is rejected by the other realm's routes at signature-verification time, before any
  database lookup -- the separation is structural, not a manual actor-type check.
- Refresh rotates the persisted token hash on every use; the previous refresh token stops
  matching any stored hash and is rejected.
- MFA challenge tokens use a separate secret, `typ=mfa_challenge`, and the issuing realm's
  audience. A challenge token cannot be used against any other route.
- Email verification and password reset tokens are opaque random tokens, not JWTs. Only HMACs
  are stored in the database (`tenant.password_reset_tokens` /
  `tenant.email_verification_tokens` for tenant users, `platform.platform_password_reset_tokens`
  / `platform.platform_email_verification_tokens` for platform admins). Both realms use the same
  underlying secrets but are physically isolated in separate tables, so a token generated for one
  realm can never validate against the other realm's table.
- Raw tokens must never be logged.

Production must set strong non-local values for every `IDENTITY_*_SECRET`.
