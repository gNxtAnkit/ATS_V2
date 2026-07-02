# Agency ATS Service Boundary

Owns agency clients, mandates, submittals, feedback, placements, guarantees, and client portal data when implemented.

Phase 0 status: directory placeholder only. No agency logic is implemented.

Rules:

- Client portal users are separate from tenant users.
- Client portal data must remain redacted and scoped.
- Agency service must not directly expose candidate master data.
- Cross-service access must use APIs, events, or approved read models.
