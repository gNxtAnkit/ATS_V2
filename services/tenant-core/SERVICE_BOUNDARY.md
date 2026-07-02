# Tenant Core Service Boundary

Owns tenant organization, RBAC/ABAC, permissions, delegations, API keys, and tenant context foundations when those phases begin.

Phase 0 status: directory placeholder only. No tenant or authorization logic is implemented.

Rules:

- Tenant-facing data must eventually be scoped by `tenant_id`.
- RLS must not be bypassed casually.
- Partner/API-key identities are governed identities, not bypass identities.
- Cross-service access must use APIs, events, or approved read models.
