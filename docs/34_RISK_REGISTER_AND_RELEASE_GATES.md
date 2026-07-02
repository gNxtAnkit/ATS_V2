# 34 — Risk Register and Release Gates

## Risk register

| Risk | Severity | Failure mode | Mitigation |
| --- | --- | --- | --- |
| Cross-tenant data leakage | Critical | API/DB/search/cache/object/event/AI leakage | RLS, composite FKs, tenant context, leakage tests |
| Platform-admin bypass | Critical | admin accesses tenant data outside support flow | separate realm/routes, support sessions, audit |
| AI autonomy too early | Critical | AI rejects/advances/messages candidates | HITL gates, autonomy config, feature flags |
| Billing error | High | duplicate/missing usage | idempotent usage events and reconciliation |
| Integration duplicates | High | webhook replay or partial sync duplicates | signature verification, idempotency, per-record sync |
| Reporting coupling | High | reports query private tables | event facts/read models |
| Compliance erasure incomplete | Critical | data remains in AI/search/object storage | DSR orchestration and erasure tests |
| Schema drift | High | ORM diverges from schema | Alembic baseline and drift CI |
| Notification consent violation | High | suppressed candidate contacted | central suppression/preferences |
| White-label spoofing | High | unverified domain maps to tenant | domain verification and CDN controls |
| Migration downtime | High | blocking/incompatible schema release | expand/migrate/contract |


## Release gates

### Foundation gate
CI green, DB baseline reproducible, validation queries pass, RLS leakage tests pass, request context implemented.

### Core platform gate
Identity, tenant core, RBAC/ABAC, platform admin, and config complete; platform-admin separation and audit tests pass.

### Core ATS gate
Candidate, corporate ATS, workflow, and agency core flows work manually with permissions/RLS/audit.

### Evented automation gate
Outbox, idempotency, notifications, integration sync, and event catalog pass tests.

### AI governance gate
AI outputs persist evidence/confidence/reasoning; HITL review cannot be bypassed; override metrics alert.

### Billing/reporting gate
Usage reconciliation, invoice tests, KPI validation, export audit, and permission filtering pass.

### Enterprise production gate
SLOs, load tests, DR restore, security scans, audit evidence, accessibility, runbooks, and incident response pass.

## Self-review checklist

Dependencies avoid AI before HITL activation, reporting before events, billing before usage, and integrations before idempotency/outbox. Tenant isolation, platform-admin separation, service ownership, audit/event flows, UI work, and test coverage are represented in every phase.
