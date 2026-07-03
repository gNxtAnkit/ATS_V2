# Platform Admin Authorization

Platform Admin Service accepts only Identity-issued platform-admin access tokens.
Tokens must use the platform-admin audience and `actor_type=platform_user`.
Tenant-user tokens are explicitly rejected before permission checks.

Authorization is role-permission based:

- `platform.platform_users`
- `platform.platform_user_roles`
- `platform.platform_roles`
- `platform.platform_role_permissions`
- `platform.platform_permissions`

The `super_admin` role receives all seeded platform permissions. Other roles
receive only their seeded permission subset. Inactive, locked, suspended, or
deleted platform users are rejected.

Administration APIs for users, roles, and permissions are grouped under:

- `/v1/platform-admin/access-control/users`
- `/v1/platform-admin/access-control/roles`
- `/v1/platform-admin/access-control/permissions`

Role-permission updates are atomic within the request transaction. System roles
cannot be deleted. The service prevents deactivating the last active super admin
and prevents a current user from removing their own final super-admin role.

Platform Admin APIs do not require normal tenant context. The service applies a
platform-admin database context with request id, actor id, and loaded platform
permissions.

Identity Service remains the owner of login, refresh, logout, password reset,
MFA, session storage, and credential security.
