# Corporate ATS Service Boundary

Owns corporate hiring workflows such as requisitions, applications, interviews, scorecards, offers, and onboarding when implemented.

Phase 0 status: directory placeholder only. No ATS logic is implemented.

Rules:

- Do not implement pipeline, requisition, application, or offer flows in Phase 0.
- Candidate data access must go through the candidate service boundary.
- Workflow automation must go through the workflow service boundary.
- Cross-service access must use APIs, events, or approved read models.
