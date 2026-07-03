# Platform Admin API

Base path: `/v1/platform-admin`.

All routes require a platform-admin access token issued by Identity Service for
the platform-admin audience. Tenant-user tokens are rejected. Every route also
requires its mapped `platform.*` permission.

Responses use the service envelope:

```json
{
  "data": {},
  "meta": { "request_id": "..." }
}
```

List responses include cursor metadata:

```json
{
  "data": [],
  "page": { "limit": 50, "next_cursor": null, "has_more": false },
  "meta": { "request_id": "..." }
}
```

Implemented route scopes:

- `Platform Admin / Dashboard`
- `Platform Admin / Tenancy`
- `Platform Admin / Tenant Domains`
- `Platform Admin / Provisioning`
- `Platform Admin / Infrastructure Pools`
- `Platform Admin / Catalogue / Plans`
- `Platform Admin / Catalogue / Quotas`
- `Platform Admin / Catalogue / Features`
- `Platform Admin / Catalogue / Add-ons`
- `Platform Admin / Entitlements`
- `Platform Admin / Feature Flags`
- `Platform Admin / Access Control`
- `Platform Admin / Support`
- `Platform Admin / Compliance`
- `Platform Admin / AI Governance`
- `Platform Admin / Operations`
- `Platform Admin / Audit Logs`

Every OpenAPI operation includes:

- `x-platform-admin-scope`
- `x-required-platform-permission`

Access-control APIs are available under the explicit scoped paths:

- `GET /access-control/users`
- `POST /access-control/users`
- `GET /access-control/users/{platform_user_id}`
- `PATCH /access-control/users/{platform_user_id}`
- `POST /access-control/users/{platform_user_id}/activate`
- `POST /access-control/users/{platform_user_id}/deactivate`
- `POST /access-control/users/{platform_user_id}/lock`
- `POST /access-control/users/{platform_user_id}/unlock`
- `GET /access-control/users/{platform_user_id}/roles`
- `PUT /access-control/users/{platform_user_id}/roles`
- `GET /access-control/roles`
- `POST /access-control/roles`
- `GET /access-control/roles/{role_id}`
- `PATCH /access-control/roles/{role_id}`
- `DELETE /access-control/roles/{role_id}`
- `GET /access-control/roles/{role_id}/permissions`
- `PUT /access-control/roles/{role_id}/permissions`
- `GET /access-control/permissions`

The original `/users`, `/roles`, and `/permissions` paths remain available for
compatibility, but the scoped access-control paths are the preferred contract.

The service returns stored records only for provisioning, deployments, error
budgets, and quality metrics. It does not fake worker execution, live monitoring,
DNS verification, AI execution, billing payments, or tenant ATS behavior.
