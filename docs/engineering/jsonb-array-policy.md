# JSONB and Array Policy

Structured business data must be relational. JSONB and arrays are allowed only for approved cases such as immutable raw payloads, audit snapshots, idempotency response snapshots, provider snapshots, or explicitly approved flexible metadata.

Validation query `14_validation_queries.sql` reports JSONB and array columns and joins them to allow-list tables:

- `platform.allowed_jsonb_columns`
- `platform.allowed_array_columns`

Rows marked `NOT ALLOWED` fail validation.
