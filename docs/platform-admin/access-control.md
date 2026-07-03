# Platform Admin Access Control

Access control APIs are grouped under `/v1/platform-admin/access-control`.

## Users

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

The Platform Admin Service manages profile/status/role assignment only. Identity
Service owns credentials, sessions, password reset, refresh, and MFA.

## Roles

- `GET /access-control/roles`
- `POST /access-control/roles`
- `GET /access-control/roles/{role_id}`
- `PATCH /access-control/roles/{role_id}`
- `DELETE /access-control/roles/{role_id}`
- `GET /access-control/roles/{role_id}/permissions`
- `PUT /access-control/roles/{role_id}/permissions`

System roles cannot be deleted. Role-permission replacement is performed in one
request transaction.

## Permissions

- `GET /access-control/permissions`

Permissions are seeded through migrations and exposed as read-only records.
Every Platform Admin route declares its required permission in OpenAPI as
`x-required-platform-permission`.
