# Billing Service Boundary

Owns subscriptions, usage, invoices, payment methods, taxes, credits, and billing reconciliation when implemented.

Phase 0 status: directory placeholder only. No billing logic is implemented.

Rules:

- Billing consumes usage events, not private AI or integration tables.
- Payment and invoice data is sensitive.
- Cross-service access must use APIs, events, or approved read models.
