# Phase 5 — Configuration Framework



## 1. Objective

Build typed config definitions, scoped values, effective resolution, caching, change log, versioning, rollback, locked settings.

## 2. Why this phase is ordered here

Tenant-specific behavior must be governed before domains hardcode settings.

## 3. Business capabilities delivered

Safe tenant/platform configuration without engineering changes.

## 4. Requirement IDs covered

CFG-11.1, CFG-11.2, CFG-11.3, MT-1.5, MT-1.6, MT-1.7, HITL-14.4 partial

## 5. Services involved

configuration service, cache invalidation worker, config UI

## 6. Owned database schemas/tables

platform.config_definitions/scope_levels/allowed_values; tenant.config_values/config_change_log

## 7. APIs to build

/v1/config/definitions, effective-values, values, change-log, rollback, validate

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

config.value.changed, config.value.rolled_back, config.cache.invalidated

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

tenant/provisioning and feature flag events

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

cache warmer, invalidator, drift validator

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

Redis/cache, secrets manager for secret refs

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

locked settings platform-only; sensitive values are secret refs

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

scope hierarchy always includes tenant_id

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

tenant config values/log RLS

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

append-only config change log and audit

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

this phase creates config dependency

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

config center, effective inspector, editor, diff, rollback

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

schema-driven forms and cache invalidation

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

precedence, cache, rollback, locked-setting, tenant leakage tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed default keys and scopes

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

read first, low-risk write, then rollback

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

effective values deterministic and auditable

## 23. Risks and edge cases

config chaos and stale cache

## 24. What must NOT be done in this phase

do not build domain logic here

## 25. Parallelization opportunities

resolver, UI, seed definitions parallel

## 26. Dependencies on previous phases

Phases 1, 3, 4

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: downstream services can consume config
