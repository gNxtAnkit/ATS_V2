# Platform Admin Service

Platform Admin Service is the internal control plane for authenticated gNxtHire
platform operators. It exposes `/v1/platform-admin` APIs for platform-owned
metadata and operations records such as tenants, lifecycle events, provisioning
jobs, plans, quotas, features, feature flags, support, compliance, AI
governance, operations metadata, and audit logs.

It does not implement platform-admin login, refresh, logout, password reset, MFA,
or sessions. Those flows are owned by Identity Service under
`/v1/identity/platform-admin`.

## Local Run

```powershell
python -m uvicorn gnxthire_platform_admin.main:app --reload --port 8002
```

## Local Tests

```powershell
python -m pytest tests/platform_admin
```

Database-backed tests require:

```powershell
$env:GNXTHIRE_RUN_DB_TESTS='1'
```

## Authorization Model

Every route requires a valid platform-admin access token issued by Identity
Service for the `gnxthire-platform-admin` audience. Tenant-user tokens are
rejected. Route handlers enforce platform permission keys loaded from
`platform.platform_user_roles`, `platform.platform_roles`,
`platform.platform_role_permissions`, and `platform.platform_permissions`.

## Boundaries

The service reads and mutates platform-owned tables. Billing subscription data is
used only for read-only entitlement context. Provisioning APIs expose stored job
records and retry/cancel state changes; they do not fake worker execution.
