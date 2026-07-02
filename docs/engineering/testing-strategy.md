# Testing Strategy

Phase 0 includes smoke tests for structure and the non-business gateway shell.

Future phases must add tests at the layer where behavior is introduced:

- Unit tests for domain rules and shared primitives.
- Integration tests for API, database, RLS, workers, outbox, notifications, and providers.
- Contract tests for OpenAPI, event schemas, provider adapters, and frontend mocks.
- Migration tests for baseline replay, drift, validation queries, and expand/migrate/contract rollout.
- Security tests for authorization, platform-admin separation, tenant leakage, and secrets handling.
- E2E tests for complete user journeys only after real product flows exist.

A phase cannot close while tenant leakage, RLS, platform-admin boundary, or high-risk audit tests are failing.
