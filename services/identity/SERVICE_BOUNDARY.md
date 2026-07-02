# Identity Service Boundary

Owns identity/session/authentication primitives only.

Phase 0 status: directory placeholder only. No identity logic is implemented.

Rules:

- Do not implement login, sessions, MFA, SSO, password reset, or user provisioning in Phase 0.
- Future service code may use shared packages from `packages/`.
- Other services must not import this service's private modules.
- Cross-service access must use APIs, events, or approved read models.
