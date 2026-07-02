# Events Service Boundary

Owns outbox, domain events, subscriptions, delivery attempts, and idempotency records when implemented.

Phase 0 status: directory placeholder only. No event delivery logic is implemented.

Rules:

- Events must use canonical envelopes.
- Consumers must be idempotent.
- Business services must not send notifications directly once events/notifications are available.
- Cross-service access must use APIs, events, or approved read models.
