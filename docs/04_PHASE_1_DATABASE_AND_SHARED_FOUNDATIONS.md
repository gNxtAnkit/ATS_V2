# Phase 1 — Database Baseline and Shared Foundations



## 1. Objective

Load PostgreSQL 16 regenerated schema, create Alembic baseline, shared backend library, request context, RLS validation, audit/event/idempotency primitives.

## 2. Why this phase is ordered here

Identity and domains cannot be safely built until RLS, tenant context, composite FKs, and baseline migrations are reproducible.

## 3. Business capabilities delivered

Trusted persistence and shared service foundation.

## 4. Requirement IDs covered

MT-1.1, MT-1.2, DATA-13.1, DATA-13.4, DATA-13.5, EVT-13.2, API-18.1, SEC-3.6, SEC-3.7, SEC-3.8

## 5. Services involved

database module, shared backend library, migration runner, model packages

## 6. Owned database schemas/tables

all schemas as baseline: platform, tenant, agency, ai, events, notif, billing, analytics, compliance, app

## 7. APIs to build

/internal/db/validate in non-prod; health endpoints

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

schema.baseline.loaded, audit.smoke.recorded

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

none

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

migration runner, validation runner, drift checker

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

PostgreSQL 16, Redis, secrets, broker/object storage abstractions

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

no DB session without tenant/platform context; crypto/secrets wrappers

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

tenant context middleware and worker context

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

run 11_rls_policies.sql and 14_validation_queries.sql; CI fails on missing RLS/tenant_id/JSONB allow-list

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

shared audit writer wrappers to platform.audit_logs and tenant.security_events

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

seed definitions read-only; config resolver later

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

developer status page only

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

standard error envelope and request id display

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

migration, RLS, cross-tenant, JSONB/array allow-list, drift tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

baseline revision; future migrations service-owned

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

dev/staging only

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

baseline loads, validates, and RLS negative tests pass

## 23. Risks and edge cases

ORM/schema drift, accidental RLS disablement

## 24. What must NOT be done in this phase

do not redesign schema, flatten schemas, remove RLS/FKs, or expose business APIs

## 25. Parallelization opportunities

models, baseline, shared primitives can parallelize

## 26. Dependencies on previous phases

Phase 0

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: identity can start
