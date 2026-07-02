# 31 — First 30 Days Execution Plan

## Goal

By day 30 the team has a runnable monorepo, local infrastructure, reproducible PostgreSQL baseline, validation gates, shared backend/frontend foundations, identity first slice, and ordered backlog for tenant/RBAC and platform admin.

## Days 1-3

Confirm architecture strategy, freeze route groups/service names, review schema ownership, create ADRs for RLS, service boundaries, outbox, platform-admin separation, and AI/HITL gating.

## Days 4-7

Create monorepo, local Docker stack, backend service skeletons, frontend shells, lint/type/test/build CI, OpenAPI lint, and route auth declaration lint.

## Days 8-12

Load schema files in numeric order, create Alembic baseline, wire validation queries, add two-tenant RLS tests, generate/author model packages, implement DB tenant context helper.

## Days 13-16

Build shared request context, actor model, error envelope, cursor pagination, idempotency middleware, audit/event envelopes, service-boundary checks, test fixtures, secrets/config interfaces.

## Days 17-21

Build identity first slice: login/logout/refresh, password hashing, sessions, email verification/reset token HMACs, security events, platform-admin login skeleton, `/me`.

## Days 22-25

Build frontend design-token foundation, tenant/platform/client/candidate shells, login/reset/MFA placeholder screens, API client interceptors, route guards.

## Days 26-30

Complete RLS/tenant leakage gate, auth integration tests, initial permission registry and seed plan, Phase 3/4 backlog, security review, demo local stack + DB validation + login + route guards + audit events.

## Day 30 exit criteria

Local stack works, DB baseline validates, RLS tests pass, shared libs are used by identity, first auth flow works, frontend shells/guards exist, and next 30-day backlog is dependency-ordered.
