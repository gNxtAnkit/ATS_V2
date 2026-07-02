# 25 — Database Migration and Model Plan

## Alembic baseline

Use the regenerated PostgreSQL 16 schema as the baseline. SQL files `00` through `13` are schema/seed baseline. `14_validation_queries.sql` is CI validation, not migration.

## SQLAlchemy model strategy

Model packages are grouped by service ownership. Preserve schema names, RLS assumptions, composite tenant-aware FKs, enum semantics, and allowed JSONB/array policy. Do not flatten into `public`.

## Migration ownership rules

- The owning service owns migrations for its tables.
- Cross-service table changes require architecture review.
- RLS policy changes require security review.
- Tenant_id/FK changes require tenant isolation review.
- Event payload changes require event catalog update.

## Validation

CI validates RLS, tenant_id presence, composite FKs, allowed JSONB columns, allowed array columns, seed idempotency, model/schema drift, and migration replay from empty DB.

## JSONB and arrays

New JSONB/array columns are rejected unless they are immutable raw/snapshot data, audit diff, idempotency response, or explicitly allow-listed. Structured business data must remain relational.

## Seed data

Seed plans, quotas, features, platform roles, tenant role templates, permissions, config definitions, connector definitions, notification templates, metric definitions, default workflows, and prompt/persona templates deterministically.

## Enum migrations

Add values before app usage, avoid removals/renames, backfill before tightening constraints, and prefer transitional states for replacements.

## Zero-downtime migrations

Use expand/migrate/contract: add nullable structures, deploy compatible app, backfill in batches, switch reads, enforce constraints, and contract in later release.
