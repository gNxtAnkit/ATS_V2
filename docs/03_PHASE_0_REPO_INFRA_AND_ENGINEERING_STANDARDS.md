# Phase 0 — Repo, Local Infrastructure, and Engineering Standards



## 1. Objective

Establish monorepo, local infra, coding standards, CI gates, service skeletons, frontend shells, API linting, and security defaults.

## 2. Why this phase is ordered here

First because every later phase needs repeatable setup, route conventions, service boundaries, and automated quality gates.

## 3. Business capabilities delivered

No customer-facing capability; delivers engineering execution reliability.

## 4. Requirement IDs covered

ARCH-19.1, ARCH-19.2, API-18.1, API-18.2, CICD-20.1, CICD-20.2, DEPLOY-17.1

## 5. Services involved

repo skeleton, shared tooling, local docker stack, CI, frontend shell placeholders

## 6. Owned database schemas/tables

none

## 7. APIs to build

/healthz, /readyz, /version, /metrics only

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

platform.service.started, platform.service.ready

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

none

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

local health checker, OpenAPI lint, dependency startup checker

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

Docker/Podman, PostgreSQL, Redis, broker, OpenSearch, object storage emulator, SMTP sink

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

default-deny route policy; no hardcoded secrets; separate route trees for platform-admin and tenant-user

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

define typed request context; no fake tenant behavior

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

placeholder RLS validation gate

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

define audit envelope only

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

define config key conventions

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

empty tenant, platform admin, client portal, and candidate shells

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

typed API client shell, auth context placeholders, error boundary

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

repo smoke, build, lint, type, import-boundary, accessibility shell tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

no business migrations

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

internal only

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

repo runs locally and CI gates are green

## 23. Risks and edge cases

scope creep and hidden business logic

## 24. What must NOT be done in this phase

do not build product features

## 25. Parallelization opportunities

infra/frontend/backend skeletons can run in parallel

## 26. Dependencies on previous phases

none

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: ready for DB baseline
