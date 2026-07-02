# Phase 16 — Reporting and Analytics Service



## 1. Objective

Build dashboards, widgets, reports, filters, columns, schedules, export jobs, metric/dimension definitions, analytics events/facts, benchmarks.

## 2. Why this phase is ordered here

Reporting must follow events/facts, not direct private table reads.

## 3. Business capabilities delivered

Operational, commercial, AI, and platform dashboards.

## 4. Requirement IDs covered

RPT-12.1-RPT-12.3, DATA-13.4, DATA-13.5, Phase 7 KPIs, PA-2.11, PA-2.12

## 5. Services involved

reporting service, analytics projector, export worker, benchmark aggregator

## 6. Owned database schemas/tables

tenant.dashboards/report_*; analytics.metric_definitions, dimension_definitions, analytics_events, metric/dimension values, daily facts

## 7. APIs to build

/v1/reports/dashboards, report-definitions, run, schedule, exports, metrics, benchmarking

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

analytics.event.ingested, report.export.completed, dashboard.shared

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

domain events, billing aggregations, HITL metrics, platform SLO events

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

event projector, daily facts, export, scheduled report sender

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

object storage, notification service

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

RBAC/ABAC and field permissions in reports/exports

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

tenant reports scoped; platform benchmarks anonymized

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

report tables RLS; facts tenant filtered

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

audit report share/export/schedule and sensitive reads

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

dashboard defaults/export limits/KPIs from config

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

dashboards, report builder, exports, standard KPI pages

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

charts with freshness and accessible table fallback

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

metric calc, projection, authorization, export, benchmark privacy tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed metrics/dimensions

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

standard dashboards then custom reports then benchmarks

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

accurate KPI dashboards from facts/events

## 23. Risks and edge cases

wrong KPIs and PII exports

## 24. What must NOT be done in this phase

do not query private operational tables from frontend

## 25. Parallelization opportunities

projector, dashboards, exports parallel

## 26. Dependencies on previous phases

Phases 10,14,15 and core domains

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: compliance and SRE can use evidence/metrics
