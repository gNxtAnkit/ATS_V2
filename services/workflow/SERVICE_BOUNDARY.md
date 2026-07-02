# Workflow Service Boundary

Owns workflow templates, steps, transitions, instances, approvals, SLAs, and history when implemented.

Phase 0 status: directory placeholder only. No workflow logic is implemented.

Rules:

- State transitions must be explicit and validated.
- Workflow must not embed corporate-ATS-specific private rules casually.
- Cross-service access must use APIs, events, or approved read models.
