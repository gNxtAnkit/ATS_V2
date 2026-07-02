# Notifications Service Boundary

Owns notification templates, preferences, suppression, deliveries, attempts, and status tracking when implemented.

Phase 0 status: directory placeholder only. No notification logic is implemented.

Rules:

- Notification scoping must preserve tenant and privacy boundaries.
- Do not query private operational tables directly for notification content.
- Cross-service access must use APIs, events, or approved read models.
