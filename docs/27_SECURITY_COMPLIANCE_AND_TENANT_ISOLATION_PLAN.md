# 27 — Security, Compliance, and Tenant Isolation Plan

## Tenant isolation layers

Auth realm, request tenant context, API authorization, service ownership, PostgreSQL RLS, composite tenant FKs, cache keys, search filters, object storage prefixes, event tenant_id, notification scoping, integration credential scoping, AI prompt context, analytics facts, and export scoping.

## Platform admin access

Platform-admin APIs are separate. Support access requires platform-admin auth, permission, reason, tenant scope, time limit, support session id, and audit. Platform-admin tokens are never accepted as tenant-user tokens.

## Sensitive data

Candidate PII, EEO, documents, salary/offers, AI transcripts/evaluations, billing/payment tokens, DSR/legal hold data, security events, and audit logs require field permissions and audit.

## Candidate privacy

Candidate master data is not exposed to client portal. Client portal sees redacted immutable submittal snapshots. Consent/suppression block outreach. DSR erasure covers documents, AI logs, search, events where required, integrations, and object storage.

## API keys and webhooks

API keys are governed identities with scopes mapped to permissions. Inbound webhooks verify provider signatures. Outbound webhooks use tenant-specific HMAC. Failed verification creates security events.

## Encryption and secrets

Use managed KMS/vault. Store secret references, not plaintext. Use signed URLs and tenant prefixes for object storage.

## Compliance controls

Retention policies, legal holds, DSR workflow, access reviews, audit retention, evidence packages, and AI governance evidence are release gates.
