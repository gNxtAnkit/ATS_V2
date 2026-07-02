# 23 — API Strategy and Route Map

## API standards

- Base path: `/v1`.
- Error envelope: `{ error: { code, message, field_errors[], request_id } }`.
- List envelope: `{ data: [], next_cursor, has_more }`.
- Cursor pagination only.
- Filters: `?filter[field][operator]=value`.
- OpenAPI required before frontend integration.
- Every route declares auth realm, tenant context rule, permission rule, rate-limit tier, idempotency rule, and audit side effects.

## Route groups

| Base path | Owning service | Main DTO groups | Auth requirements | Idempotency/rate limit | Audit/event side effects |
| --- | --- | --- | --- | --- | --- |
| /v1/identity/... | Identity | auth/session/MFA/SSO DTOs | realm-specific; no tenant until resolved | auth rate limits; reset/verify idempotent | security events |
| /v1/platform-admin/... | Platform Admin | tenant/admin/support/plan DTOs | platform-admin realm only | idempotency for mutations | platform audit |
| /v1/tenants/... | Tenant Core | tenant/user/team/calendar/branding DTOs | tenant user + tenant_id | invite/update idempotency | tenant audit |
| /v1/rbac/... | RBAC/ABAC | role/permission/policy DTOs | tenant authz admin | versioned policy updates | authz audit |
| /v1/config/... | Config | definition/value/change-log DTOs | tenant or platform scope | version/checksum | config events |
| /v1/candidates/... | Candidate | profile/document/consent DTOs | tenant + field perms | document/import idempotency | candidate audit |
| /v1/corporate-ats/... | Corporate ATS | req/application/interview/offer DTOs | tenant + business-unit perms | submit/stage idempotency | ATS events |
| /v1/workflows/... | Workflow | template/instance/approval DTOs | tenant + approver/delegate | decision idempotency | workflow history |
| /v1/agency-ats/... | Agency ATS | client/mandate/submittal DTOs | tenant + client_id where portal | submittal idempotency | agency audit |
| /v1/events/... | Events | event/subscription/replay DTOs | service/platform/tenant scoped | event idempotency | replay audit |
| /v1/notifications/... | Notifications | template/preference/delivery DTOs | tenant + recipient privacy | send/test idempotency | delivery events |
| /v1/integrations/... | Integrations | connector/sync/webhook DTOs | tenant integration admin; signed webhooks | sync/webhook idempotency | integration audit |
| /v1/ai-recruiter/... | AI Recruiter | persona/prompt/screening DTOs | tenant + AI agent permissions | AI run idempotency | AI usage/review events |
| /v1/interviews/... | AI Interview | session/question/evaluation/call DTOs | tenant or limited candidate token | media/eval/call idempotency | consent/review events |
| /v1/hitl/... | HITL | review/decision/autonomy DTOs | tenant reviewer permissions | decision idempotency | HITL audit |
| /v1/billing/... | Billing | subscription/usage/invoice DTOs | tenant billing admin or platform support | payment/usage idempotency | billing events |
| /v1/reports/... | Reporting | dashboard/report/export DTOs | tenant RBAC/ABAC | export idempotency | report audit |
| /v1/compliance/... | Compliance | DSR/retention/legal-hold/evidence DTOs | compliance permissions | DSR task idempotency | compliance audit |


## Versioning strategy

Breaking changes require a new version and migration guide. Additive changes remain in `/v1`. Deprecated versions trigger usage-based notifications and enterprise deprecation windows.

## Idempotency requirements

Mandatory for provisioning, invites, password/reset, candidate imports, document upload completion, requisition submit, workflow start, approval decisions, submittals, notifications, provider webhooks, sync jobs, AI runs, HITL decisions, usage events, payment webhooks, invoice generation, and DSR task actions.

## Rate-limit requirements

Rate limits apply by route group, actor, tenant, IP, API key, and provider. AI, telephony, partner API, and webhook traffic have separate quotas from interactive UI traffic.
