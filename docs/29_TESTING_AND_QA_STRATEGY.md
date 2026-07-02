# 29 — Testing and QA Strategy

## Required test layers

- Unit tests for domain rules, config, authz decisions, workflow conditions, billing math, AI safety policies.
- Integration tests for API + DB with RLS enabled, workers, outbox, notifications, webhooks, payments.
- Contract tests for OpenAPI, event schemas, provider adapters, frontend mocks.
- Migration tests for baseline, validation queries, drift, expand/migrate/contract.
- RLS isolation tests for every tenant route/table.
- API authorization tests for all route groups.
- Tenant leakage tests across API, DB, cache, search, object storage, events, notifications, analytics, exports, and AI prompts.
- Platform-admin boundary tests.
- Workflow, outbox, idempotency, notification retry, billing metering, AI/HITL, compliance erasure tests.
- Performance/load/noisy-neighbor tests.
- Security scans, penetration tests, secrets scan, dependency scan.
- E2E tests for corporate requisition-to-hire, agency mandate-to-placement, candidate journey, platform admin support, AI+HITL, billing, DSR.
- Accessibility tests for all shells and critical workflows.

## Exit rule

A phase cannot close if tenant leakage, RLS, platform-admin boundary, or high-risk audit tests are failing.
