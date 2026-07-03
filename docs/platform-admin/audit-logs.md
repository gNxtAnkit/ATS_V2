# Platform Audit Logs

Platform Admin Service writes `platform.audit_logs` for every implemented
mutation.

Audit entries include:

- request id
- actor type and platform user id
- action key
- object schema/table/id
- tenant id when applicable
- redacted before/after/diff snapshots
- IP address and user agent when available

Audit logs are read-only through the Platform Admin API. Sensitive fields such
as passwords, secrets, tokens, API keys, credentials, and session values are
redacted before audit snapshots are stored.
