# Database Ownership Rules

Phase 1 loads the regenerated PostgreSQL 16 baseline through Alembic. The SQL package remains the database source of truth.

## Ownership

- The owning service owns migrations for its tables.
- Cross-service table changes require architecture review.
- RLS policy changes require security review.
- `tenant_id` and foreign-key changes require tenant isolation review.
- Event payload changes require event catalog updates.

## Shared Database, Strict Ownership

PostgreSQL is shared initially, but schemas and table groups remain private to their owner services. Reporting, billing, notifications, integrations, and AI services must not infer behavior by querying private operational tables.

## Tenant Isolation

Tenant-facing data must eventually be tenant-scoped. RLS must remain enabled and forced for tenant-scoped tables. RLS must not be bypassed casually for support, testing, reporting, or background jobs.

## Migration Policy

Migrations must be additive, deterministic, reviewed, and compatible with expand/migrate/contract rollout. Destructive changes require an explicit safe rollout plan.
