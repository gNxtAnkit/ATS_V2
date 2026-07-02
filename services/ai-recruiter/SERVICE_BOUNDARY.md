# AI Recruiter Service Boundary

Owns recruiter personas, prompt templates, agent identities, sourcing, matching, screening, conversations, scheduling, and AI usage events when implemented.

Phase 0 status: directory placeholder only. No AI logic is implemented.

Rules:

- AI agents are permission-scoped system actors.
- Candidate-impacting AI actions require HITL, audit, configuration, and governance controls.
- Do not implement AI automation in Phase 0.
- Cross-service access must use APIs, events, or approved read models.
