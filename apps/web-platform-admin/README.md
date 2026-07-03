# Platform Admin Web

Standalone React application for Gnxthire platform administrators.

This app is intentionally isolated from tenant-facing web apps. It calls the platform-admin identity surface and the Platform Admin control-plane API:

- `/v1/identity/platform-admin`
- `/v1/identity/platform-users`
- `/v1/platform-admin`

The Bolt UI folder in this repository is the source design base. Keep its admin shell, auth flow, dense panels, buttons, alerts, inputs, and navigation patterns as the visual reference when extending this app.

## Local setup

```bash
npm install
npm run dev
```

By default the app talks to `http://localhost:8001`. Override that with:

```bash
VITE_IDENTITY_API_BASE_URL=http://localhost:8001 npm run dev
```

Set the Platform Admin API base URL with:

```bash
VITE_PLATFORM_ADMIN_API_BASE_URL=http://localhost:8002 npm run dev
```

The app uses browser history routing, so URLs are normal paths such as `/login` and `/security`; it does not use hash routes such as `#/auth/login`.

## Local test data

From the repository root:

```bash
make up
make db-upgrade
make seed-platform-admin
```

Seeded local users use `LocalTest@12345`; see `docs/seeding/platform-admin-seed-data.md`.

## API smoke coverage

```bash
make smoke-platform-admin-api
```

The smoke script writes `artifacts/platform-admin-api-coverage.md`.

## Validation

```bash
npm run typecheck
npm run lint
npm run build
```
