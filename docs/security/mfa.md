# MFA

Both tenant users and platform admins use standards-compatible TOTP, implemented once in
`security.py` and applied identically by `gnxthire_identity.tenant` (against
`tenant.user_mfa_factors`) and `gnxthire_identity.platform_admin` (against
`platform.platform_user_mfa_factors`).

- Setup returns `provisioning_uri` and `manual_entry_secret` once.
- Pending setup is stored with `disabled_at` set and a protected `secret_ref` prefixed with
  `pending:`. This prevents a previously disabled factor from being mistaken for an active
  setup attempt. MFA is **not** enabled until confirmation.
- Confirmation verifies the TOTP code, clears `disabled_at`, and returns recovery codes once.
- Recovery codes are stored only as HMACs using `method='recovery_code'`, and each is single-use
  (`consume_recovery_code` sets `disabled_at` on the exact matching row).
- Login returns `status="mfa_required"`, `mfa_required=true`, a short-lived,
  purpose-limited challenge token, available methods, and the challenge expiry when a primary
  TOTP factor is enabled. The response does not include normal access or refresh tokens.
- MFA challenge tokens cannot access any normal API route because they verify against
  `typ=mfa_challenge` and a separate MFA challenge secret, not `typ=access`.
- Successful `mfa/totp/verify` completes login and issues a normal access/refresh token pair for
  the caller's realm.
- Setup is rejected with a conflict when MFA is already enabled.
- Disabling MFA and regenerating recovery codes require the current password, not just an
  authenticated session. Both operations require MFA to already be enabled.
- `GET /auth/me` is the UI source of truth for `mfa_enabled`, configured methods, pending
  setup, and remaining recovery-code count. The UI must not infer MFA state from local storage
  or setup page state.
- Unsupported MFA methods such as SMS, push, and WebAuthn are not exposed in production UI.
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
