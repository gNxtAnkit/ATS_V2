# Configuration Service Boundary

Owns typed configuration definitions, scoped values, change history, and effective configuration resolution when implemented.

Phase 0 status: directory placeholder only. No configuration logic is implemented.

Rules:

- Tenant-specific behavior must be configuration-driven once config keys exist.
- Do not hardcode domain behavior that belongs in the configuration framework.
- Cross-service access must use APIs, events, or approved read models.
