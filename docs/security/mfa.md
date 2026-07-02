# MFA

Both tenant users and platform admins use standards-compatible TOTP, implemented once in
`security.py` and applied identically by `gnxthire_identity.tenant` (against
`tenant.user_mfa_factors`) and `gnxthire_identity.platform_admin` (against
`platform.platform_user_mfa_factors`).

- Setup returns `provisioning_uri` and `manual_entry_secret` once.
- Pending setup is stored with `disabled_at` set -- MFA is **not** enabled until confirmation.
- Confirmation verifies the TOTP code, clears `disabled_at`, and returns recovery codes once.
- Recovery codes are stored only as HMACs using `method='recovery_code'`, and each is single-use
  (`consume_recovery_code` sets `disabled_at` on the exact matching row).
- Login returns `status="mfa_required"` with a short-lived, purpose-limited
  `mfa_challenge_token` when a primary TOTP factor is enabled. That token cannot access any
  normal API route (it verifies against `typ=mfa_challenge`, not `typ=access`).
- Successful `mfa/totp/verify` completes login and issues a normal access/refresh token pair for
  the caller's realm.
- Disabling MFA requires the current password (`disable_mfa`), not just an authenticated
  session.
- Configuration (`MFA_TOTP_ISSUER`, `MFA_TOTP_DIGITS`, `MFA_TOTP_INTERVAL_SECONDS`,
  `MFA_TOTP_VALID_WINDOW`, `MFA_RECOVERY_CODE_COUNT`, `MFA_RECOVERY_CODE_LENGTH`) is shared by
  both realms.

TOTP secrets are protected (`encrypt_secret`/`decrypt_secret`, `IDENTITY_MFA_SECRET_ENCRYPTION_KEY`)
before database storage in the `secret_ref` column. Raw TOTP secrets and recovery codes must not
be logged.

Platform admins additionally have a `platform.platform_users.mfa_required` flag settable by
another authenticated platform admin via `POST /v1/identity/platform-users/{id}/require-mfa`.
This is a real, persisted, audited flag intended for compliance tracking (which admins are
required to have MFA configured). **It does not currently block login** for an admin who hasn't
completed TOTP setup yet: doing so safely would require issuing a distinct, setup-scoped-only
token (since reaching `mfa/totp/setup` itself requires an authenticated bearer token, and a full
access token cannot be withheld without one to bootstrap setup with). That step-up token type is
out of Phase 2 scope and is not implemented -- this is a known, explicitly documented limitation,
not a silent gap.
