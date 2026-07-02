# gNxtHire

gNxtHire is an AI-native, multi-tenant ATS platform. This repository contains the Phase 0 foundation and Phase 1 database/shared backend foundations.

The repository intentionally does not implement ATS, identity/auth flows, onboarding, RBAC APIs, platform-admin business flows, candidate CRUD, workflow runtime, agency, AI, billing, reporting, notification delivery, or integration business logic yet.

## Quick Start

1. Install Python 3.12+.
2. Copy `.env.example` to `.env` and keep the safe local defaults unless you know why they need to change.
3. Run `make setup`.
4. Run `make up` to start local infrastructure.
5. Run `make db-upgrade` to create the database baseline.
6. Run `make db-validate` to execute schema governance checks.
7. Run `make quality` before opening a pull request.

See [Local Development](docs/engineering/local-development.md) for details.

## Repository Shape

- `apps/`: API gateway and frontend app shells.
- `services/`: bounded-context service skeletons.
- `packages/`: shared backend, frontend, contracts, and testing packages.
- `db/`: schema, migrations, seeds, and validation placeholders.
- `infra/`: local and future deployment infrastructure.
- `scripts/`: fail-fast developer automation.
- `tests/`: unit, integration, contract, security, and e2e test roots.

## Current Foundation

- Alembic uses generated SQLAlchemy models under `db/models` for the Phase 1 initial migration.
- `db/schema/14_validation_queries.sql` is validation-only.
- `packages/backend-common` contains shared settings, DB, RLS context, request context, logging redaction, errors, pagination, idempotency, and model base primitives.
- The API gateway exposes only non-business health/version endpoints.
- Service directories document ownership and intended boundaries.

Next phase: Identity Service implementation.
