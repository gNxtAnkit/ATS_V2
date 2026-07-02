# Phase 18 — White-Labeling, Internationalization, and Mobile Readiness



## 1. Objective

Complete branding, custom domains, localization, mobile device registrations, push readiness, responsive shells, selected offline flows.

## 2. Why this phase is ordered here

Do after real surfaces exist so branding/i18n/mobile cover real workflows consistently.

## 3. Business capabilities delivered

Enterprise branded, localized, mobile-ready UX.

## 4. Requirement IDs covered

MOB-21.1, MOB-21.2, BRAND-21.3, I18N-21.4, I18N-21.5, MT-1.6, MT-1.8

## 5. Services involved

branding service, localization service, mobile device service, frontend platform

## 6. Owned database schemas/tables

tenant.tenant_branding, white_label_domains, localization_resources, mobile_device_registrations, domain_verifications

## 7. APIs to build

/v1/tenants/branding, white-label-domains, localization-resources, /v1/identity/mobile-devices

All APIs must follow the standard `/v1` envelope, include `request_id`, document auth requirements in OpenAPI, use cursor pagination for lists, and require idempotency keys for duplicate-prone mutations.

## 8. Events published

branding.updated, white_label_domain.verified, localization.changed, mobile_device.registered

All published events use the canonical event envelope and are inserted through the outbox when they follow a database mutation.

## 9. Events consumed

tenant provisioning, config, notification template changes

Consumers must be idempotent and may update only their owned tables/read models.

## 10. Background jobs/workers

domain verification, localization cache invalidation, push cleanup

Workers must set tenant context, record attempts, expose metrics, and use bounded retry/backoff.

## 11. External providers involved

DNS/CDN, push providers, TMS optional

Provider integrations must start with sandbox/fake adapters and secret references.

## 12. Security and authorization rules

verified domains only; revocable mobile devices

Server-side authorization is mandatory; UI hiding is not sufficient.

## 13. Tenant isolation rules

branding tenant/client scoped; host mapping verified

Tenant isolation applies to API, DB, cache, search, object storage, events, notifications, integrations, reports, and AI prompt context.

## 14. RLS/database requirements

branding/localization/mobile RLS

RLS validation and cross-tenant negative tests are required before completion.

## 15. Audit/event requirements

audit domain, branding, locale, mobile changes

Audit records must include actor, realm, tenant, entity, action, request id, support session id where applicable, and before/after/diff where relevant.

## 16. Configuration dependencies

locale fallback, enabled languages, mobile flags from config

Tenant-specific behavior must be driven by the configuration framework where a config key exists or is appropriate.

## 17. UI screens/pages/components to build

branding editor, domain setup, localization editor, responsive shells

Use the shared design system, permission-aware actions, standardized loading/error/empty states, and audit-sensitive confirmation dialogs.

## 18. Frontend state/data-fetching requirements

theme resolver, locale loader, mobile-safe forms, offline queue for selected flows

Use typed API clients, tenant-scoped query keys, route guards, and central error handling with request id display.

## 19. Test plan

domain, hostname, theme isolation, locale fallback, mobile guard, accessibility tests

Also include unit, integration, contract, authorization, RLS, tenant leakage, idempotency, audit, and frontend route-guard tests where applicable.

## 20. Migration/data requirements

seed localization keys

Migrations are additive, service-owned, reviewed for tenant isolation, and validated against schema drift checks.

## 21. Rollout plan

branding then locale then domains then mobile/offline

Rollout must use feature flags, internal tenants, seeded data, and explicit rollback notes.

## 22. Definition of done

all shells resolve correct brand/locale

## 23. Risks and edge cases

hostname spoofing and brand leakage

## 24. What must NOT be done in this phase

do not fork frontend per tenant

## 25. Parallelization opportunities

branding, i18n, mobile, accessibility parallel

## 26. Dependencies on previous phases

Phases 3,5,10 and stable UI domains

## 27. Handoff checklist for the next phase

- OpenAPI and event catalog updated.
- Service-to-table ownership matrix updated.
- Required permissions and config keys documented.
- RLS, authorization, tenant leakage, idempotency, and audit tests pass.
- Frontend routes are guarded and permission-aware.
- Runbooks and rollback notes are present.
- Handoff: production SRE can validate domains/mobile
