# Environment Variables

`.env.example` documents safe local defaults. Secrets must not be committed.

## Current Phase 1 Variables

- `GNXTHIRE_ENV`: local environment name.
- `GNXTHIRE_APP_NAME`: display/application name for service metadata.
- `GNXTHIRE_SERVICE_NAME`: service name used by the gateway shell.
- `GNXTHIRE_VERSION`: local service version string.
- `GNXTHIRE_DEBUG`: local debug flag. Must be false in production.
- `GNXTHIRE_LOGGING_LEVEL`: structured logging level.
- `GNXTHIRE_REQUEST_ID_HEADER`: inbound request id header name.
- `GNXTHIRE_CORRELATION_ID_HEADER`: inbound correlation id header name.
- `GNXTHIRE_ENFORCE_RLS_CONTEXT`: enables tenant/platform context enforcement.
- `GNXTHIRE_RUN_MIGRATIONS_ON_STARTUP`: defaults to false.
- `GNXTHIRE_RUN_DATABASE_VALIDATION_ON_STARTUP`: defaults to false.
- `DATABASE_URL`: SQLAlchemy-compatible PostgreSQL connection string.
- `TEST_DATABASE_URL`: optional PostgreSQL connection string for DB-dependent tests.
- `REDIS_URL`: Redis connection string.
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka-compatible broker bootstrap servers.
- `OPENSEARCH_URL`: local OpenSearch endpoint.
- `MAILPIT_SMTP_HOST`, `MAILPIT_SMTP_PORT`, `MAILPIT_UI_URL`: local email sink settings.

## Rules

- Store secret references, not plaintext secrets, in production configuration.
- Production must provide explicit `DATABASE_URL` and `REDIS_URL`; local defaults are rejected.
- Do not add permissive fallback identities or tenant IDs.
- New environment variables must be documented here and validated at service startup.
