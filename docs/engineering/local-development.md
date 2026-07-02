# Local Development

## Requirements

- Python 3.12+
- Docker or a compatible container runtime
- `make`

## Setup

```bash
cp .env.example .env
make setup
make up
make db-upgrade
make db-validate
make quality
```

## Local Infrastructure

`docker-compose.yml` starts safe local defaults:

- PostgreSQL 16 with pgvector on `localhost:45432`
- Redis on `localhost:6379`
- Redpanda Kafka-compatible broker on `localhost:9092`
- OpenSearch on `localhost:9200`
- Mailpit SMTP on `localhost:1025`, UI on `localhost:8025`

These services are for local development only. They do not contain production secrets.

## API Gateway Shell

Run:

```bash
make dev
```

The gateway shell exposes only `/healthz`, `/readyz`, `/version`, and `/metrics`.
