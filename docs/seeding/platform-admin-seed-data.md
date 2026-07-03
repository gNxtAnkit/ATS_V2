# Platform Admin Local/Test Seed Data

The Platform Admin seed is local/test only and refuses to run when either `GNXTHIRE_ENVIRONMENT` or `APP_ENV` is outside `local` or `test`.

## Run

```bash
make up
make db-upgrade
make seed-platform-admin
```

Reset only the Platform Admin local/test seed rows:

```bash
make seed-platform-admin-reset
```

The seed is idempotent and re-runnable. It uses the real Identity password hashing utility and never stores plaintext passwords in the database.

## Seeded Credentials

Local/test password for all seeded users:

```text
LocalTest@12345
```

Platform admins:

- `super.admin@local.gnxthire.test`
- `support.admin@local.gnxthire.test`
- `billing.admin@local.gnxthire.test`
- `security.admin@local.gnxthire.test`
- `ai.governance@local.gnxthire.test`
- `auditor@local.gnxthire.test`

Tenant-user rejection smoke user:

- `tenant.admin@local.gnxthire.test`

## Seeded Data

The seed creates roles, permissions, platform users, infra pools, plans, quotas, features, plan entitlements, add-ons, tenants, tenant domains, provisioning jobs and steps, feature flags and overrides, support sessions, support tickets, SLA policies, compliance frameworks and regions, tenant compliance mappings, AI model metadata, AI quality metrics, governance alerts, API version metadata, deployments, SLO/error budget data, and audit rows.

## Safety

Do not run these scripts in production. The scripts are intentionally designed for local/manual QA and automated smoke validation only.
