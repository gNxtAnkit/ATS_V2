# Identity Email Delivery

Local development uses Mailpit/Mailhog-compatible SMTP defaults:

```text
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
SMTP_USE_SSL=false
SMTP_FROM_EMAIL=no-reply@local.gnxthire.com
```

Start the local stack, then open the Mailpit UI at `http://localhost:8025`.

Production checklist:

- Set real SMTP host, port, TLS/SSL mode, username, and password when required.
- Set frontend verification and reset URLs, including `FRONTEND_PLATFORM_ADMIN_PASSWORD_RESET_URL`
  (a separate URL/frontend from the tenant-user reset URLs -- platform admins reset from a
  different app).
- Set strong non-local identity secrets.
- Keep `IDENTITY_EMAIL_DELIVERY_ENABLED=true` only when SMTP is configured.
- Confirm no raw token values appear in logs.

Both tenant-user and platform-admin flows send through the same `SmtpEmailSender` /
`EmailSender` protocol (`gnxthire_identity.email`) -- there is one SMTP adapter, not two. What
differs per realm is only which frontend base URL (`FRONTEND_PASSWORD_RESET_URL` vs.
`FRONTEND_PLATFORM_ADMIN_PASSWORD_RESET_URL`) is used to build the link, and which token table
the link's token is checked against.

The Identity Service owns this SMTP adapter until the Notification Service replaces it
through the same `EmailSender` interface.
