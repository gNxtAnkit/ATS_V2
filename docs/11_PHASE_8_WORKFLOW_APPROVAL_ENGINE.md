# Phase 8 — Workflow and Approval Engine



## 1. Objective

Build workflow templates, canvas metadata, steps, transitions, conditions, instances, approvals, SLAs, escalations, simulation, history.

## 2. Why this phase is ordered here

Approval automation should be reusable and follow first corporate domain data model.

## 3. Business capabilities delivered

Governed approvals and workflow execution.

## 4. Requirement IDs covered

WF-5.1-WF-5.7, CAT-4.3, RBAC-6.2, RBAC-6.3, HITL-14.4 partial

## 5. Services involved

workflow engine, approval task service, SLA/escalation worker

## 6. Owned database schemas/tables

tenant.workflow_* tables, entity_references, approval_tasks, ai_action_autonomy_configs

## 7. APIs to build

/v1/workflows/templates, publish, simulate, instances, approval-tasks, approve/reject/delegate

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

workflow.instance.started, workflow.approval.requested, workflow.sla.breached, workflow.instance.completed

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

corporate events, config changes, RBAC delegations

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

SLA monitor, reminders producer, timeout handler

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

notification service later

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

approver/delegate only; no unsafe condition code

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

workflow entity refs must stay tenant scoped

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

workflow tables RLS and composite references

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

append-only workflow and approval history

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

SLA/default templates from config

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

workflow builder, approval inbox, simulation, history

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

task polling, version diff, condition builder

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

graph validation, routing, delegation, SLA, idempotent start tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed default workflows

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

requisition approvals first

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

approval chain works with audit/SLA

## 23. Risks and edge cases

too-general engine; lost history

## 24. What must NOT be done in this phase

do not execute AI actions or send notifications directly

## 25. Parallelization opportunities

template, task, SLA, UI parallel

## 26. Dependencies on previous phases

Phases 3,5,7

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: agency/AI/HITL can reuse workflow
