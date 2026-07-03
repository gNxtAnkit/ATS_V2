# Platform Admin API Endpoint Coverage

Generated: 2026-07-02T09:28:52.489224+00:00

| Method | Endpoint | Status | Auth Tested | Permission Tested | Audit Tested | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/v1/platform-admin/dashboard/summary` | passed | 401/403 | auditor mutation 403 | n/a | Auth and tenant-token rejection verified. |
| POST | `/v1/platform-admin/tenants` | passed | token | super_admin | mutation | HTTP 200 |
| DELETE | `/v1/platform-admin/access-control/roles/{role_id}` | skipped | token | destructive | not-tested | Skipped in broad smoke because system seeded roles are protected. |
| DELETE | `/v1/platform-admin/feature-flags/{flag_id}/tenant-overrides/{tenant_id}` | skipped | token | destructive | not-tested | Skipped in broad smoke to preserve shared seeded overrides. |
| DELETE | `/v1/platform-admin/tenants/{tenant_id}/domains/{domain_id}` | skipped | token | destructive | not-tested | Skipped in broad smoke to preserve shared seeded domains. |
| GET | `/v1/platform-admin/access-control/permissions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/access-control/roles` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/access-control/roles/{role_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/access-control/roles/{role_id}/permissions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/access-control/users` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/access-control/users/{platform_user_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/access-control/users/{platform_user_id}/roles` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/addons` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/addons/{addon_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/addons/{addon_id}/features` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/addons/{addon_id}/quota-deltas` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/ai/governance-alerts` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/ai/governance-alerts/{alert_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/ai/models` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/ai/models/{model_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/ai/models/{model_id}/region-restrictions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/ai/quality-metrics` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/api-versions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/audit-logs` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/audit-logs/{audit_log_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/compliance/frameworks` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/compliance/frameworks/{framework_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/compliance/frameworks/{framework_id}/regions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/deployments` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/deployments/{deployment_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/error-budgets` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/feature-flags` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/feature-flags/{flag_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/feature-flags/{flag_id}/tenant-overrides` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/features` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/features/{feature_definition_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/infra-pools` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/infra-pools/{infra_pool_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/plans` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/plans/{plan_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/plans/{plan_id}/features` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/plans/{plan_id}/quotas` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/provisioning-jobs` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/provisioning-jobs/{job_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/quotas` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/quotas/{quota_definition_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/sla-policies` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/sla-policies/{sla_policy_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/slo-definitions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/support-sessions` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/support-sessions/{support_session_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/support-tickets` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/support-tickets/{ticket_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/compliance-frameworks` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/domains` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/effective-entitlements` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/health` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/lifecycle-events` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/provisioning-jobs` | passed | token | super_admin | read-only | HTTP 200 |
| GET | `/v1/platform-admin/tenants/{tenant_id}/subscription-summary` | passed | token | super_admin | read-only | HTTP 200 |
| PATCH | `/v1/platform-admin/access-control/roles/{role_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/access-control/users/{platform_user_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/addons/{addon_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/ai/models/{model_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/api-versions/{api_version_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/compliance/frameworks/{framework_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/feature-flags/{flag_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/features/{feature_definition_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/infra-pools/{infra_pool_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/plans/{plan_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/quotas/{quota_definition_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/sla-policies/{sla_policy_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/slo-definitions/{slo_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/support-tickets/{ticket_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/tenants/{tenant_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PATCH | `/v1/platform-admin/tenants/{tenant_id}/domains/{domain_id}` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/access-control/roles` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/access-control/users` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/access-control/users/{platform_user_id}/activate` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/access-control/users/{platform_user_id}/deactivate` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/access-control/users/{platform_user_id}/lock` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/access-control/users/{platform_user_id}/unlock` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/addons` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/addons/{addon_id}/activate` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/addons/{addon_id}/retire` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/ai/governance-alerts/{alert_id}/acknowledge` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/ai/governance-alerts/{alert_id}/resolve` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/ai/models` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/api-versions` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/compliance/frameworks` | passed | token | super_admin | mutation | HTTP 409 |
| POST | `/v1/platform-admin/feature-flags` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/features` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/infra-pools` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/infra-pools/{infra_pool_id}/activate` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/infra-pools/{infra_pool_id}/deactivate` | passed | token | super_admin | mutation | HTTP 409 |
| POST | `/v1/platform-admin/plans` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/plans/{plan_id}/activate` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/plans/{plan_id}/retire` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/provisioning-jobs/{job_id}/cancel` | passed | token | super_admin | mutation | HTTP 409 |
| POST | `/v1/platform-admin/provisioning-jobs/{job_id}/retry` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/quotas` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/sla-policies` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/slo-definitions` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/support-sessions` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/support-sessions/{support_session_id}/end` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/support-tickets` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/support-tickets/{ticket_id}/assign` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/support-tickets/{ticket_id}/close` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/tenants/{tenant_id}/activate` | skipped | token | state-sensitive | not-tested | Skipped in broad smoke to avoid corrupting shared seeded tenants. |
| POST | `/v1/platform-admin/tenants/{tenant_id}/churn` | skipped | token | state-sensitive | not-tested | Skipped in broad smoke to avoid corrupting shared seeded tenants. |
| POST | `/v1/platform-admin/tenants/{tenant_id}/domains` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/tenants/{tenant_id}/domains/{domain_id}/verify` | passed | token | super_admin | mutation | HTTP 200 |
| POST | `/v1/platform-admin/tenants/{tenant_id}/reactivate` | skipped | token | state-sensitive | not-tested | Skipped in broad smoke to avoid corrupting shared seeded tenants. |
| POST | `/v1/platform-admin/tenants/{tenant_id}/restore` | skipped | token | state-sensitive | not-tested | Skipped in broad smoke to avoid corrupting shared seeded tenants. |
| POST | `/v1/platform-admin/tenants/{tenant_id}/soft-delete` | skipped | token | state-sensitive | not-tested | Skipped in broad smoke to avoid corrupting shared seeded tenants. |
| POST | `/v1/platform-admin/tenants/{tenant_id}/suspend` | skipped | token | state-sensitive | not-tested | Skipped in broad smoke to avoid corrupting shared seeded tenants. |
| PUT | `/v1/platform-admin/access-control/roles/{role_id}/permissions` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/access-control/users/{platform_user_id}/roles` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/addons/{addon_id}/features` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/addons/{addon_id}/quota-deltas` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/ai/models/{model_id}/region-restrictions` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/compliance/frameworks/{framework_id}/regions` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/feature-flags/{flag_id}/tenant-overrides/{tenant_id}` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/plans/{plan_id}/features` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/plans/{plan_id}/quotas` | passed | token | super_admin | mutation | HTTP 200 |
| PUT | `/v1/platform-admin/tenants/{tenant_id}/compliance-frameworks` | passed | token | super_admin | mutation | HTTP 200 |
