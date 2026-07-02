# Platform Admin Service Boundary

Owns the separate platform-admin control plane.

Phase 0 status: directory placeholder only. No platform-admin logic is implemented.

Rules:

- Platform-admin APIs must stay separate from tenant-user APIs.
- Platform-admin access must be reason-coded, time-bound, scoped, and audited.
- Platform-admin access is not a general tenant data bypass.
- Cross-service access must use APIs, events, or approved read models.
