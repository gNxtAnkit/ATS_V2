# CI Quality Gates

The Phase 0 CI skeleton runs:

- Install
- Ruff format check
- Ruff lint
- Mypy typecheck
- Unit tests
- DB schema artifact check
- Security/static analysis placeholder

Database migration and validation tests are available locally with `GNXTHIRE_RUN_DB_TESTS=1` and a real PostgreSQL database. CI currently performs the schema artifact check without starting the database service. Security/static analysis remains a labeled placeholder until scanners are selected.
