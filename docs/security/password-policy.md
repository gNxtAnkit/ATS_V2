# Password Policy

Password policy is configured by:

- `PASSWORD_MIN_LENGTH`
- `PASSWORD_MAX_LENGTH`
- `PASSWORD_REQUIRE_UPPERCASE`
- `PASSWORD_REQUIRE_LOWERCASE`
- `PASSWORD_REQUIRE_NUMBER`
- `PASSWORD_REQUIRE_SPECIAL`
- `PASSWORD_PREVENT_EMAIL_SIMILARITY`

Passwords are hashed with PBKDF2-HMAC-SHA256 using per-password random salts. Raw passwords
must never be logged, emitted in events, or stored.
