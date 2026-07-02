# 24 — Frontend Implementation Plan

## App shells

- Tenant user app shell: recruiters, hiring managers, tenant admins, HR/finance, interviewers.
- Platform admin app shell: gNxtHire operators, support, governance, billing ops.
- Client portal shell: agency client contacts scoped by `client_id`.
- Candidate-facing shell: application, consent, interview, and status flows with limited tokens.

## Design system foundation

Use shared tokens for typography, color, spacing, radius, elevation, density, focus, status, and AI-specific indicators. Components must support permission-hidden, disabled-with-reason, audit confirmation, loading, empty, error, and degraded states.

## Route guards

Auth realm guard, tenant context guard, permission guard, feature flag guard, client_id guard, candidate limited token guard, and platform support-session guard.

## Navigation

Navigation is permission-aware and feature-flag-aware. Platform-admin navigation never appears in tenant app. Client portal never shows candidate master/internal ATS settings. Candidate shell never exposes internal routes.

## API client structure

One generated typed client per route group. Interceptors handle auth, request id, tenant context, idempotency key, standard error envelope, and refresh/logout. Query keys include tenant id and actor realm.

## Critical screens

Auth screens, tenant settings, platform admin console, config center, candidate profile, corporate requisition/pipeline, workflow approvals, agency client portal, notification center, integration marketplace, AI review surfaces, HITL queue, billing, reports, compliance, white-label/i18n/mobile settings.

## Error/loading/empty states

Every page must have skeleton, empty, forbidden, failed, and partial degraded states. Errors show request id. Sensitive auth errors do not reveal existence.

## Audit-sensitive confirmations

Required for deletes/restores, role grants, field permissions, support sessions, feature flags, config rollback, candidate erasure, legal holds, payment changes, AI autonomy changes, bulk HITL approvals, sync replay, webhook replay, invoice void/credit.

## Soft-delete/restore

Deleted records hidden by default. Restore screens show who/when/why and require permission and reason.

## Accessibility

Keyboard navigation, focus states, contrast, screen reader labels, error announcements, and chart table fallback are release gates.
