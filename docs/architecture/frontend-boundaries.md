# Frontend Boundary Expectations

Phase 0 creates app placeholders only. No ATS screens or production workflows are implemented.

## App Separation

- `apps/web-tenant`: tenant user app.
- `apps/web-platform-admin`: separate platform-admin app and route tree.
- `apps/web-client-portal`: external client portal, separate from tenant users.
- `apps/web-candidate`: candidate-facing flows, separate from internal users.
- `packages/frontend-common`: shared UI, route guard, navigation, and query conventions.

## Required Future Patterns

- Route guards must enforce expected realm and tenant context.
- Navigation must be permission-aware.
- Navigation must respect feature flags.
- Data-fetching keys must include tenant context when tenant-scoped.
- UI authorization is only user experience; backend authorization remains mandatory.
- Loading, empty, error, permission-denied, and partial-data states must be explicit.
