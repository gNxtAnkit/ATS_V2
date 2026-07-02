# Database Setup

## Local Database

Start local infrastructure:

```bash
make up
```

The local PostgreSQL service uses `pgvector/pgvector:pg16` because the baseline requires the `vector` extension.
It binds to host port `45432` to avoid collisions with an existing PostgreSQL on `5432`.

Apply the baseline:

```bash
make db-upgrade
make db-current
make db-validate
```

Reset the local baseline:

```bash
make db-reset-local
```

`db-reset-local` refuses to run when `GNXTHIRE_ENV=production`.

## Alembic Baseline

The baseline revision is `0001_initial_schema.py`. It imports `db.models.Base.metadata` and creates model-backed tables through SQLAlchemy metadata. The raw SQL files remain reference artifacts and validation inputs, not the primary migration mechanism.

The migration handles PostgreSQL-specific objects manually:

- schemas
- extensions
- app context and trigger functions
- the unused `data_tier_enum` type
- default partition child tables
- RLS enablement and policies
- triggers
- views
- schema/table comments
- seed/reference data

Future migrations must be service-owned and additive unless an approved expand/migrate/contract plan exists.

## Troubleshooting

- If `CREATE EXTENSION vector` fails, confirm the database image includes pgvector.
- If validation reports missing RLS, run `make db-upgrade` and confirm `11_rls_policies.sql` executed.
- If JSONB or array validation returns `NOT ALLOWED`, either normalize the structure or add an approved allow-list row in the regenerated schema with architecture review.
- If Alembic is not on the expected head, run `make db-current` and `make db-history`.
