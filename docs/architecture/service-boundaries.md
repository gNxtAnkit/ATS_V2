# Service Boundary Rules

gNxtHire starts as a microservice-oriented monorepo using a shared PostgreSQL database. Code boundaries must be treated as real service boundaries even before services are extracted.

## Rules

- A service may write only tables it owns.
- Private tables are not shared because they live in the same database.
- Cross-service reads should happen through APIs, domain events, read models, or approved views.
- Workers follow the same boundaries as APIs.
- Shared code belongs only in `packages/`.
- Services must not import another service's private modules.
- Platform-admin access is not a tenant data bypass.

## Separate Realms

- Platform-admin APIs stay separate from tenant-user APIs.
- Client portal users are separate from tenant users.
- Candidate-facing flows are separate from internal user flows.
- Partner/API-key identities are governed identities with explicit scopes.

## Future Extraction Criteria

A bounded context can move to an independent service/database only after it has stable OpenAPI contracts, stable event contracts, no private imports from other services, runbooks, owned migrations, and contract tests.
