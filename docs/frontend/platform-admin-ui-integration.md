# Platform Admin UI Integration

The Platform Admin UI lives in `apps/web-platform-admin`.

## Environment

```bash
VITE_IDENTITY_API_BASE_URL=http://localhost:8001
VITE_PLATFORM_ADMIN_API_BASE_URL=http://localhost:8002
```

## Run

```bash
cd apps/web-platform-admin
npm install
npm run dev
```

The UI keeps Identity calls separate from Platform Admin service calls. Identity owns login, refresh, logout, MFA, password reset, email verification, and credential status flows. Platform Admin service calls are made through `platformControlApi`.

## Implemented Behavior

- platform-admin login through Identity
- MFA challenge verification
- forgot/reset password and email verification
- session refresh on 401
- logout
- permission-aware Platform Admin navigation
- live dashboard summary
- live module pages for tenants, provisioning, plans/catalogue, feature flags, access control, support, compliance, AI governance, operations, and audit logs
- safe action buttons where a real seeded API action can be executed
- loading, empty, error, and permission-denied states

The UI does not use production mock data for Platform Admin modules.
