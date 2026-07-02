# RLS and Tenant Context

PostgreSQL RLS uses transaction-local settings read by helper functions such as
`app.current_tenant_id()`, `app.current_user_id()`, `app.is_platform_admin()`, and
`app.has_permission()`.

Application code must set context inside the request or worker transaction:

- `app.current_tenant_id`
- `app.user_id`
- `app.actor_type`
- `app.permissions`
- `app.is_platform_admin`
- `app.platform_admin_id`
- `app.request_id`
- `app.correlation_id`

Use `gnxthire_common.rls.set_tenant_context()` for tenant-facing queries and
`gnxthire_common.rls.set_platform_admin_context()` for platform-admin queries.
Both helpers use PostgreSQL `set_config(..., true)` so values are scoped to the
current transaction.

## Rules

- Tenant-facing database access requires a tenant context.
- Platform-admin database access must be explicit and separately named.
- Platform-admin access is not a silent tenant bypass.
- Support-session access must carry platform-admin context and be audited by the owning service.
- Runtime application connections must not use superuser credentials.
- Do not create raw SQL helpers that skip tenant context silently.
- Do not pass platform-admin context into tenant-user code paths as a fallback identity.
