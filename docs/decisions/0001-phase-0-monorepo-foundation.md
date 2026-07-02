# ADR 0001: Phase 0 Monorepo Foundation

## Status

Accepted

## Context

gNxtHire needs a foundation that allows teams and coding agents to work safely across many bounded contexts without prematurely implementing product logic.

## Decision

Use a microservice-oriented monorepo with a transitional shared-PostgreSQL model. Create service directories, shared packages, local infrastructure, developer commands, CI gates, and documentation before implementing business features.

## Consequences

- Future service extraction remains possible.
- Shared code has an explicit home in `packages/`.
- Service-private modules must not be imported casually.
- Phase 1 can add the database baseline without reshaping the repository.
