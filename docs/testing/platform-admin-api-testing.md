# Platform Admin API Testing

## Prerequisites

Run Postgres and migrations, then seed local/test data:

```bash
make up
make db-upgrade
make seed-platform-admin
```

Start Identity and Platform Admin services in separate terminals. Defaults used by the smoke script:

- Identity: `http://localhost:8001`
- Platform Admin: `http://localhost:8002`

Override with:

```bash
IDENTITY_API_BASE_URL=http://localhost:8001 PLATFORM_ADMIN_API_BASE_URL=http://localhost:8002 make smoke-platform-admin-api
```

## Smoke Test

```bash
make smoke-platform-admin-api
```

The smoke script:

- logs in through Identity as the `PLATFORM_ADMIN_SEED_EMAIL` user
- logs in as `auditor@local.gnxthire.test`
- logs in as a tenant user and verifies Platform Admin APIs reject that token
- verifies unauthenticated access fails
- verifies a read-only auditor cannot run a plan mutation
- calls Platform Admin endpoints through HTTP
- writes `artifacts/platform-admin-api-coverage.md`

The script exits non-zero when any endpoint is not covered by a safe scenario.

## Notes

The script assumes seeded data exists. It does not fake responses and does not bypass authentication or Platform Admin permission checks.
