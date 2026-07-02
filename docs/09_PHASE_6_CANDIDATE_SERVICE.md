# Phase 6 — Candidate Service



## 1. Objective

Build candidate master profiles, contacts, documents, consent, suppressions, talent pools, duplicate flags, skills, work/education, EEO-sensitive handling.

## 2. Why this phase is ordered here

ATS, agency, AI, integrations, reporting, and compliance all reference candidates.

## 3. Business capabilities delivered

Recruiters can manage candidate data safely.

## 4. Requirement IDs covered

SEC-3.9, DATA-13.1, DATA-13.5, CAT-4.7 partial, AAT-7.6, INT-10.3 partial

## 5. Services involved

candidate service, document metadata, duplicate worker, consent helper

## 6. Owned database schemas/tables

tenant.candidates, candidate_contacts, candidate_documents, consent_records, DSR tasks, talent_pools, suppressions, skills, EEO, duplicate flags

## 7. APIs to build

/v1/candidates, contacts, documents, skills, work-history, education, consents, suppressions, duplicates, talent-pools, search

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

candidate.created, candidate.updated, candidate.consent.recorded, candidate.suppressed, candidate.duplicate_flagged

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

identity, future job-board events, legal hold

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

duplicate detection, search indexing, consent expiry, document scan placeholder

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

object storage, malware scan, search index

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

PII/EEO field permissions; signed document URLs; suppression blocks outreach

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

candidate master never exposed to client portal; tenant scoped only

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

candidate tables RLS; search index tenant filter

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

audit candidate changes, document access, consent, suppression, EEO access

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

consent/document/duplicate thresholds from config

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

candidate list/profile, document, consent, duplicate, talent pool screens

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

field masking and signed URL flow

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

CRUD authz, masking, RLS, document access, suppression tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed skill taxonomy carefully

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

manual create then docs then duplicate advisory

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

candidate lifecycle with consent/audit/RLS works

## 23. Risks and edge cases

PII leakage and premature hard-delete

## 24. What must NOT be done in this phase

do not build ATS pipeline or submittals

## 25. Parallelization opportunities

CRUD, docs, consent, search parallel

## 26. Dependencies on previous phases

Phases 1,2,3,5

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: ATS/agency can reference candidates
