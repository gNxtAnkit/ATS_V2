# Reporting Service Boundary

Owns dashboards, reports, analytics events, dimensions, metrics, facts, schedules, and exports when implemented.

Phase 0 status: directory placeholder only. No reporting logic is implemented.

Rules:

- Reporting consumes events and facts, not private operational tables.
- Exports must be tenant-scoped and audited.
- Cross-service access must use APIs, events, or approved read models.
