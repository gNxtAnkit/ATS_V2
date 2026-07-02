# Integrations Service Boundary

Owns connector definitions, tenant connector instances, sync jobs, webhooks, and provider adapters when implemented.

Phase 0 status: directory placeholder only. No integration logic is implemented.

Rules:

- Inbound webhooks must verify provider signatures.
- Integrations require idempotency and outbox before provider-specific work.
- Store secret references, not plaintext secrets.
- Cross-service access must use APIs, events, or approved read models.
