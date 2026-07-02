# API Gateway Shell

Phase 0 exposes only non-business platform endpoints:

- `GET /healthz`
- `GET /readyz`
- `GET /version`
- `GET /metrics`

Business route groups must be added in later phases only after their service contracts, authorization requirements, tenant context behavior, and tests are defined.
