# SQLAlchemy Model Conventions

The database SQL is the source of truth. SQLAlchemy models must reflect it, not redesign it.

## Current Model Coverage

Phase 1 now uses the generated `db/models` package for Alembic metadata.

- ORM table models: 282.
- Explicit non-model default partition tables: 6.
- PostgreSQL enum/domain objects are declared in `db/models/core.py`.
- All model modules are imported through `db/models/__init__.py`.

The raw SQL table inventory and model registry are checked by `make db-check`.

## Rules

- Preserve PostgreSQL schema names.
- Preserve composite tenant-aware foreign keys.
- Do not flatten models into one file.
- Do not invent columns or omit important constraints when SQLAlchemy can represent them.
- Do not put service-specific business logic in model classes.
- PostgreSQL-only objects such as RLS policies, trigger functions, triggers, views, extensions, seed data, and default partition children belong in Alembic operations.
