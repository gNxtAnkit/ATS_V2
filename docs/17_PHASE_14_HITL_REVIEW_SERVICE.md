# Phase 14 — Human-in-the-Loop Review Service



## 1. Objective

Build unified review queue, routing, decisions, modifications, related items, autonomy configs, override metrics, governance alerts.

## 2. Why this phase is ordered here

AI outputs exist but cannot affect candidates safely until HITL is complete.

## 3. Business capabilities delivered

Humans approve/modify/reject AI outputs with audit and governance feedback.

## 4. Requirement IDs covered

HITL-14.1-HITL-14.4, WF-5.5, AIR-8.5, AIB-9.5, PA-2.12, PA-2.16

## 5. Services involved

HITL service, routing engine, decision service, governance metric worker

## 6. Owned database schemas/tables

tenant.review_items, review_item_relations, human_decisions, ai_action_autonomy_configs, platform.ai_quality_metrics/governance_alerts

## 7. APIs to build

/v1/hitl/review-items, approve, reject, modify, assign, autonomy-configs, override-metrics

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

hitl.review_item.approved, hitl.review_item.modified, hitl.override_rate.threshold_breached

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

ai.review_required, interview.review_required, workflow AI step events

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

SLA monitor, assignment worker, override aggregator, continuation worker

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

notification service

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

reviewer RBAC/ABAC; original and modified output preserved

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

review queue tenant scoped; platform sees aggregates unless support session

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

review tables RLS

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

audit every decision, diff, assignment, autonomy change

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

autonomy modes and thresholds from config

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

unified queue, detail, evidence, diff editor, autonomy settings

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

filters, mandatory reason dialogs, related context

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

routing, decisions, modifications, SLA, autonomy, RLS tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed autonomy configs/reason codes

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

mandatory review first; limited autonomy later

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

AI actions continue only after permitted decision

## 23. Risks and edge cases

queue overload and misconfigured autonomy

## 24. What must NOT be done in this phase

do not enable unrestricted AI

## 25. Parallelization opportunities

API/UI/routing/metrics parallel

## 26. Dependencies on previous phases

Phases 8,10,12,13

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: billing/reporting/compliance can consume review events
