# Phase 17 — Compliance, Privacy, and Retention Service



## 1. Objective

Build DSR workflows, consent governance, retention policies, legal holds, evidence packages, erasure orchestration, access reviews.

## 2. Why this phase is ordered here

Full compliance requires mature data across domains, AI, events, billing, reports, integrations.

## 3. Business capabilities delivered

Enterprise privacy and compliance readiness.

## 4. Requirement IDs covered

SEC-3.8, SEC-3.9, DATA-13.5, PA-2.13, PA-2.14, RPT-12.3, Phase 7 risk/readiness

## 5. Services involved

compliance service, DSR orchestrator, retention worker, evidence service

## 6. Owned database schemas/tables

compliance.retention_policies, legal_holds, evidence_packages/items; tenant consent/DSR/security; platform audit/compliance frameworks

## 7. APIs to build

/v1/compliance/consents, dsr, retention-policies, legal-holds, evidence-packages, access-reviews, erasure-certificates

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

compliance.dsr.created, compliance.erasure.completed, compliance.legal_hold.created, compliance.evidence_package.generated

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

candidate erasure, legal hold, audit/security, AI, integration, report events

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

DSR orchestrator, erasure handlers, retention purge, evidence compiler

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

object storage, notification service

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

legal hold blocks erasure; evidence encrypted/access-controlled

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

tenant admins see only tenant compliance

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

compliance RLS; workers set tenant context

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

audit all DSR, erasure, legal hold, evidence actions

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

retention/SLA/frameworks from config

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

compliance dashboard, DSR queue, legal holds, evidence builder

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

high-risk confirmations and progress timelines

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

DSR, legal hold, retention, erasure, evidence, leakage tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed frameworks/retention

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

tracking/export before erasure and purge

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

erasure request tracked across domains with certificate

## 23. Risks and edge cases

incomplete erasure or deletion under hold

## 24. What must NOT be done in this phase

do not hard delete blindly

## 25. Parallelization opportunities

DSR, retention, evidence parallel

## 26. Dependencies on previous phases

Core domains, events, AI, reporting

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: enterprise readiness can validate compliance
