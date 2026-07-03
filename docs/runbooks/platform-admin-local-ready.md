# Platform Admin Local Ready Runbook

Use this runbook after local containers, volumes, or database state were deleted and you need a fresh Platform Admin environment.

These steps intentionally do not use the Makefile.

## What This Produces

- Local infrastructure running from `docker-compose.yml`.
- PostgreSQL initialized on `localhost:45432`.
- Alembic migrations applied through the current head.
- Platform Admin seed data loaded.
- A local Platform Admin user with all rights:
  - Email: `.env` value `PLATFORM_ADMIN_SEED_EMAIL`, default `ankit@gnxtsystems.com`
  - Password: `.env` value `PLATFORM_ADMIN_SEED_PASSWORD`, default `LocalTest@12345`
  - Role: `super_admin`

The seed script is local/test only. It refuses to run when the environment is not local or test.

## 1. Open PowerShell At The Repository Root

```powershell
cd C:\Users\ankit\Agentic_Apps\ats-v2
```

## 2. Create Local Environment File

Skip this step if `.env` already exists and contains local settings.

```powershell
Copy-Item .env.example .env
```

Confirm these values are present in `.env`:

```text
GNXTHIRE_ENV=local
APP_ENV=local
DATABASE_URL=postgresql+psycopg://gnxthire:gnxthire_local_password@localhost:45432/gnxthire_local
REDIS_URL=redis://localhost:6379/0
PLATFORM_ADMIN_SEED_EMAIL=ankit@gnxtsystems.com
PLATFORM_ADMIN_SEED_PASSWORD=LocalTest@12345
```

## 3. Install Python Dependencies

```powershell
python -m pip install -e ".[dev]"
```

## 4. Start Local Infrastructure

```powershell
docker compose up -d
```

Check that the containers are running:

```powershell
docker compose ps
```

Expected local ports:

- PostgreSQL: `localhost:45432`
- Redis: `localhost:6379`
- Redpanda: `localhost:9092`
- OpenSearch: `localhost:9200`
- Mailpit UI: `http://localhost:8025`

## 5. Apply Database Migrations

```powershell
python scripts/db.py upgrade
```

Confirm the migration head:

```powershell
python scripts/db.py current
```

Expected head:

```text
0003_platform_admin_perms
```

## 6. Validate The Database

```powershell
python scripts/db.py validate
```

This checks the migrated database schema, expected extensions, schemas, tables, enum/domain types, and baseline platform seed plans.

## 7. Seed Platform Admin Data

```powershell
python scripts/platform_admin_seed_data.py
```

Expected output includes:

```text
Seeded Platform Admin local/test data.
Local password: LocalTest@12345
- ankit@gnxtsystems.com (super_admin)
```

The `super_admin` role is assigned every permission defined by `scripts/platform_admin_seed_data.py`.

## 8. Verify The Super Admin Role And Permissions

```powershell
$seedEmail = (Select-String -Path .env -Pattern '^PLATFORM_ADMIN_SEED_EMAIL=').Line -replace '^PLATFORM_ADMIN_SEED_EMAIL=', ''
docker compose exec postgres psql -U gnxthire -d gnxthire_local -v seed_email="$seedEmail" -c "SELECT u.email, r.role_key, count(p.permission_key) AS permission_count FROM platform.platform_users u JOIN platform.platform_user_roles ur ON ur.platform_user_id = u.id JOIN platform.platform_roles r ON r.id = ur.role_id LEFT JOIN platform.platform_role_permissions rp ON rp.role_id = r.id LEFT JOIN platform.platform_permissions p ON p.id = rp.permission_id WHERE u.email = :'seed_email' GROUP BY u.email, r.role_key;"
```

Expected result:

- `email` matches `PLATFORM_ADMIN_SEED_EMAIL`
- `role_key` is `super_admin`
- `permission_count` is greater than `0`

## 9. Start Identity Service

Open a new PowerShell terminal at the repository root:

```powershell
cd C:\Users\ankit\Agentic_Apps\ats-v2
python -m uvicorn gnxthire_identity.main:app --reload --port 8001
```

Verify it responds:

```powershell
Invoke-RestMethod http://localhost:8001/openapi.json
```

## 10. Start Platform Admin API

Open another PowerShell terminal at the repository root:

```powershell
cd C:\Users\ankit\Agentic_Apps\ats-v2
python -m uvicorn gnxthire_platform_admin.main:app --reload --port 8002
```

Verify it responds:

```powershell
Invoke-RestMethod http://localhost:8002/openapi.json
```

## 11. Start Platform Admin Web App

Open another PowerShell terminal:

```powershell
cd C:\Users\ankit\Agentic_Apps\ats-v2\apps\web-platform-admin
npm install
$env:VITE_IDENTITY_API_BASE_URL="http://localhost:8001"
$env:VITE_PLATFORM_ADMIN_API_BASE_URL="http://localhost:8002"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/login
```

Log in with:

```text
Email: the `PLATFORM_ADMIN_SEED_EMAIL` value from `.env`
Password: the `PLATFORM_ADMIN_SEED_PASSWORD` value from `.env`
```

## 12. Optional API Login Check

With Identity Service running:

```powershell
$seedEmail = (Select-String -Path .env -Pattern '^PLATFORM_ADMIN_SEED_EMAIL=').Line -replace '^PLATFORM_ADMIN_SEED_EMAIL=', ''
$seedPassword = (Select-String -Path .env -Pattern '^PLATFORM_ADMIN_SEED_PASSWORD=').Line -replace '^PLATFORM_ADMIN_SEED_PASSWORD=', ''
$body = @{ email = $seedEmail; password = $seedPassword } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8001/v1/identity/platform-admin/auth/login `
  -ContentType "application/json" `
  -Body $body
```

Expected result: a JSON response containing platform-admin access and refresh token fields.

## Reset Options

### Re-run Only The Seed

The Platform Admin seed is idempotent and can be run again:

```powershell
python scripts/platform_admin_seed_data.py
```

### Reset Only Local Platform Admin Seed Rows

```powershell
python scripts/reset_platform_admin_seed.py
python scripts/platform_admin_seed_data.py
```

### Rebuild The Local Database Baseline

Use this when the local database exists but is in a bad local state:

```powershell
python scripts/db.py reset-local
python scripts/platform_admin_seed_data.py
```

### Recreate Deleted Containers

If only containers were deleted and named Docker volumes still exist:

```powershell
docker compose up -d
python scripts/db.py current
python scripts/platform_admin_seed_data.py
```

If containers and volumes were both deleted, start again from step 4.

## Troubleshooting

### Port Already In Use

Check what is using the port, stop that process, or choose another service port:

```powershell
netstat -ano | findstr :8001
netstat -ano | findstr :8002
netstat -ano | findstr :5173
```

### Database Connection Fails

Confirm PostgreSQL is running:

```powershell
docker compose ps postgres
docker compose logs postgres
```

Then confirm `.env` points at:

```text
localhost:45432
```

### Login Fails

Run the seed again:

```powershell
python scripts/platform_admin_seed_data.py
```

Then confirm the user exists:

```powershell
$seedEmail = (Select-String -Path .env -Pattern '^PLATFORM_ADMIN_SEED_EMAIL=').Line -replace '^PLATFORM_ADMIN_SEED_EMAIL=', ''
docker compose exec postgres psql -U gnxthire -d gnxthire_local -v seed_email="$seedEmail" -c "SELECT email, status, email_verified_at IS NOT NULL AS email_verified FROM platform.platform_users WHERE email = :'seed_email';"
```

Expected result:

- `status` is `active`
- `email_verified` is `t`
