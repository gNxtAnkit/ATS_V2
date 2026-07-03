# Tenant Management

Tenant creation writes:

- `platform.tenants` with `status=provisioning`
- `platform.tenant_provisioning_jobs` with `status=pending`
- pending provisioning steps
- `platform.tenant_lifecycle_events`
- `platform.audit_logs`
- `events.event_outbox` event `platform.tenant.created`

Tenant creation requires an idempotency key. The key is stored on the
provisioning job for duplicate detection within the tenant provisioning record.

Lifecycle transitions are explicit and reject invalid transitions. Suspend,
churn, and soft-delete require a reason. Tenants are not physically deleted.

Provisioning APIs expose stored job and step records. Retry is allowed only for
failed or partial-failure jobs. Cancel is allowed only for pending or running
jobs. No provisioning worker success is faked by the API.
