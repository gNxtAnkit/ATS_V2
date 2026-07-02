# Repository Structure

The repository uses a microservice-oriented monorepo with a transitional shared-PostgreSQL model.

## Top-Level Areas

- `apps/`: user-facing application shells and API gateway/BFF.
- `services/`: bounded-context service directories. Each service owns its private implementation.
- `packages/`: shared packages for cross-service foundations and contracts.
- `db/`: schema, migrations, seeds, and validation gates.
- `infra/`: local and deployment infrastructure.
- `scripts/`: fail-fast developer automation.
- `tests/`: test suites grouped by layer.
- `docs/`: architecture, engineering, runbooks, and decisions.

## Phase 0 Rule

Only infrastructure and standards belong in Phase 0. Business features, fake APIs, mock production flows, and database redesigns are out of scope.
