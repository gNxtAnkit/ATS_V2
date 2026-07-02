# Database Migrations

Phase 1 uses a single model-driven Alembic initial revision.

## Baseline Strategy

- `db/models` is the source Alembic imports for table metadata.
- SQLAlchemy metadata creates tables, columns, primary keys, foreign keys, composite tenant-aware foreign keys, check constraints, unique constraints, indexes, server defaults, PostgreSQL enums, and domains.
- PostgreSQL-specific objects that SQLAlchemy cannot fully represent are explicit operations in `0001_initial_schema.py`.
- `14_validation_queries.sql` is validation-only and must not be executed as a migration.
- Future migrations are service-owned and should be additive by default.
- The baseline downgrade is intended for local/dev reset paths.

Rules:

- Owning services own migrations for their tables.
- Cross-service table changes require architecture review.
- RLS policy changes require security review.
- Tenant isolation changes require dedicated tests.
