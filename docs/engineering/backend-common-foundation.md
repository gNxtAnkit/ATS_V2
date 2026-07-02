# Backend Common Foundation

Phase 1 shared backend code lives in `packages/backend-common/src/gnxthire_common`.
It is infrastructure only. It must not contain login, tenant onboarding, RBAC APIs, ATS
flows, candidate workflows, billing behavior, notification delivery, AI behavior, or other
service business logic.

## Configuration

Use `gnxthire_common.config.Settings` or `get_settings()` for runtime configuration.
Settings are loaded with `pydantic-settings` and support safe local defaults.

Important variables:

- `GNXTHIRE_ENV`: `local`, `test`, `dev`, `qa`, `staging`, or `production`.
- `GNXTHIRE_SERVICE_NAME`: service process name.
- `DATABASE_URL`: PostgreSQL SQLAlchemy URL using `postgresql+psycopg`.
- `TEST_DATABASE_URL`: optional database URL for DB-dependent tests.
- `REDIS_URL`: Redis connection URL.
- `GNXTHIRE_LOGGING_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `GNXTHIRE_ENFORCE_RLS_CONTEXT`: keeps tenant/platform context checks enabled.
- `GNXTHIRE_RUN_MIGRATIONS_ON_STARTUP`: defaults to false.
- `GNXTHIRE_RUN_DATABASE_VALIDATION_ON_STARTUP`: defaults to false.

Production settings fail fast when database or Redis URLs are not explicitly supplied,
when SQL echo/debug is enabled, or when the database URL points to localhost.

## Database Sessions

Use `create_sync_engine()`, `create_session_factory()`, and `session_scope()` for sync
SQLAlchemy 2.x access. Runtime service databases must use PostgreSQL. Tests may create
their own local SQLAlchemy engines for isolated helper behavior.

`session_scope()` commits on success **and** on a handled `AppError` subclass (auth,
validation, rate-limit, conflict, etc.) raised inside the block, since those errors are
deliberate outcomes and any writes made before raising them (most importantly
security/audit event rows written on a failure path) must persist even though the
request itself returns an error response. It rolls back only for exceptions that are
not `AppError`, where the transaction state is not trustworthy.

Rules:

- Do not use superuser-only behavior in application code.
- Do not add generic raw-SQL helpers that bypass tenant context.
- Wrap multi-step writes in one transaction boundary.
- Use the caller service's owned tables only. Cross-service reads should happen through
  APIs, events, read models, or approved views.

## RLS Context

Use `set_tenant_context()` for tenant-facing operations and
`set_platform_admin_context()` for platform-admin operations. These helpers set
transaction-local PostgreSQL variables with `set_config(..., true)`.

Current variables:

- `app.current_tenant_id`
- `app.user_id`
- `app.actor_type`
- `app.is_platform_admin`
- `app.platform_admin_id`
- `app.permissions`
- `app.request_id`
- `app.correlation_id`

Tenant-facing operations require `tenant_id`. Platform-admin operations must be explicit
and must not masquerade as tenant-user operations. `clear_context()` is available for
tests and defensive cleanup, but normal request code should rely on transaction-local
scope.

## Request Context

`RequestContext` carries request id, correlation id, actor id/type, tenant id,
platform-admin id, support session id, source IP, user agent, and auth/session
placeholders for later phases. Phase 2 Identity should construct this after auth
validation and pass it into DB, logging, and API error helpers.

## Logging

Use `redact_mapping()`, `log_extra()`, and `context_log_fields()` for structured logs.
Sensitive keys containing password, secret, token, API key, authorization, credential, or
session are redacted recursively.

Do not log candidate-sensitive data, raw credentials, bearer tokens, password reset
tokens, provider secrets, or unredacted request payloads.

## Error Envelope

Use `AppError` subclasses and `build_error_envelope()`/`error_to_envelope()` for API
errors. The stable shape is:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Invalid request",
    "field_errors": [],
    "request_id": "req_123"
  }
}
```

Do not expose stack traces or internal SQL/provider details in API responses.

## Pagination

Use cursor pagination only. `CursorPayload`, `encode_cursor()`, `decode_cursor()`, and
`CursorPage` provide the shared primitives. Offset pagination is not the default.

## Idempotency

`IdempotencyKey`, `fingerprint_request()`, `ResponseSnapshot`, and
`IdempotencyRepository` define reusable primitives. They do not implement service-specific
idempotency behavior. Future APIs must store records in the existing `events`
idempotency schema through their service transaction boundary.

## Health and Readiness

`HealthCheckResult`, `AppHealthResult`, `database_health_check()`, and
`redis_health_check()` distinguish liveness/readiness building blocks. Services may expose
health endpoints later, but Phase 1 does not create public business APIs.

## Database Validation

Use these commands from Windows PowerShell:

```powershell
python scripts/db.py upgrade
python scripts/db.py current
python scripts/db.py heads
python scripts/db.py check
python scripts/db.py validate
python -m pytest tests/integration/test_migrations.py
```

DB-dependent tests require a running PostgreSQL container and:

```powershell
$env:GNXTHIRE_RUN_DB_TESTS="1"
```

## Phase 2 Handoff

Identity Service should reuse:

- `Settings` for configuration.
- `RequestContext` after authentication succeeds.
- `set_tenant_context()` and `set_platform_admin_context()` before tenant/platform DB work.
- `AppError` and the standard error envelope.
- cursor pagination and idempotency primitives for duplicate-prone APIs.
- health primitives for service readiness.
