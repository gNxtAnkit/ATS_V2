# Phase 3 — Tenant Core, RBAC, and ABAC Authorization



## 1. Objective

Build tenant org, users, business units, teams, roles, permissions, role assignments, ABAC, field permissions, delegations, API keys, calendars, branding basics.

## 2. Why this phase is ordered here

Domain services need authorization, user/org structure, and scoped permissions before exposing sensitive data.

## 3. Business capabilities delivered

Tenant admins can configure organization and secure access.

## 4. Requirement IDs covered

MT-1.3, MT-1.4, MT-1.5, MT-1.6 partial, SEC-3.4, SEC-3.5, RBAC-6.1, RBAC-6.2, RBAC-6.3, RBAC-6.4, API-18.3 partial

## 5. Services involved

tenant core service, RBAC/ABAC service, API-key governance

## 6. Owned database schemas/tables

platform.tenants/domains; tenant.business_units, users, teams, roles, permissions, ABAC, field_permissions, delegations, api_keys, calendars

## 7. APIs to build

/v1/tenants/..., /v1/rbac/roles, permissions, assignments, abac-policies, field-permissions, delegations, api-keys

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

tenant.user.invited, tenant.role.changed, tenant.abac_policy.changed, tenant.api_key.revoked

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

identity events

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

invitation expiry, delegation expiry, permission cache invalidation

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

email via notification later, secrets for API keys

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

all routes require explicit permission; field permissions enforced server-side; API keys are governed identities

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

tenant scoped user/org access only; client_id scope reserved for agency portal

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

all tenant core tables RLS; permission cache includes tenant_id

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

audit user, role, permission, ABAC, delegation, API key changes

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

default roles/permissions seeded; full config resolver used

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

tenant settings, users, roles, permissions, teams, API keys, calendar pages

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

permission-aware navigation and guarded actions

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

RBAC/ABAC, field mask, API key, tenant leakage tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed default roles/permissions

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

internal tenants first

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

authz middleware mandatory and tested

## 23. Risks and edge cases

permission cache leakage; UI-only enforcement

## 24. What must NOT be done in this phase

do not expose candidate/requisition data

## 25. Parallelization opportunities

RBAC engine, UI, API keys parallel

## 26. Dependencies on previous phases

Phase 2

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: platform admin and config can rely on authz
