# Candidate Service Boundary

Owns candidate master records, contact data, documents, consent, suppression, talent pools, and candidate-sensitive data when implemented.

Phase 0 status: directory placeholder only. No candidate logic is implemented.

Rules:

- Candidate PII access must be minimized and audited.
- Candidate-facing flows are separate from internal user flows.
- Client portal users must not receive candidate master data directly.
- Cross-service access must use APIs, events, or approved read models.
