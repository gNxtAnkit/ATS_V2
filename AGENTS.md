# AGENTS.md

## Purpose

This file defines mandatory engineering rules for autonomous coding agents such as Codex, Cursor, Cline, and similar AI coding tools working in this repository.

The agent must behave like a careful Staff Software Engineer. The goal is not to generate a large amount of code quickly. The goal is to produce correct, maintainable, readable, testable, production-grade code that a professional engineering team can confidently review, extend, and operate.

These instructions apply to every code change, refactor, migration, test, configuration change, documentation update, and bug fix.

---

# 1. Core Philosophy

## 1.1 Production code first

Write code as if it will run in production, be reviewed by senior engineers, debugged during incidents, and maintained for years.

Do not write throwaway code unless the user explicitly asks for a temporary prototype. Even then, clearly isolate prototype code and label it as non-production.

## 1.2 Prefer clarity over cleverness

The best code is simple, obvious, and boring.

Prefer straightforward control flow, explicit names, small functions, and clear boundaries. Avoid clever abstractions, excessive indirection, or patterns that make the code harder to understand.

## 1.3 Preserve existing behavior unless change is requested

Do not rewrite unrelated systems. Do not change behavior outside the requested scope. Do not “improve” surrounding code unless it is necessary for the task and the reason is clear.

Every change must have a direct purpose tied to the request.

## 1.4 Small, safe, reviewable changes

Prefer small, coherent changes that can be reviewed independently. Avoid massive rewrites. Avoid touching many files unless the task truly requires it.

When a change spans multiple layers, keep each layer cleanly separated:

- Data model
- Domain logic
- API or interface
- UI or client behavior
- Tests
- Documentation

## 1.5 Respect architecture and ownership

Follow the repository’s existing architecture, naming conventions, module boundaries, and dependency direction.

Do not bypass service boundaries, database ownership rules, authorization checks, validation layers, or shared abstractions.

---

# 2. Mandatory Agent Workflow

Before editing code, the agent must understand the task and the current implementation.

## 2.1 Inspect first

Always inspect relevant files before modifying them. Do not guess file paths, symbols, schemas, route names, models, functions, or dependencies.

Use repository search and existing code patterns before creating anything new.

## 2.2 Plan before changing

For non-trivial changes, produce a short implementation plan before editing. The plan must identify:

- Files likely to be changed
- Existing behavior being preserved
- New behavior being added
- Tests to add or update
- Risks or edge cases

Do not proceed with broad changes without understanding the current code path.

## 2.3 Change only what is necessary

Keep the diff focused. Do not perform unrelated cleanup, formatting, dependency upgrades, renames, or architecture changes in the same task unless explicitly requested.

## 2.4 Validate after changes

After editing, run the smallest relevant validation command available:

- Unit tests for touched code
- Type checking
- Linting
- Formatting checks
- Migration validation
- Build checks

If a command cannot be run, state that clearly and explain why.

## 2.5 Report honestly

At the end of the task, report:

- What changed
- Files changed
- Tests or checks run
- Any checks not run
- Any remaining risks or follow-up work

Never claim success without evidence.

---

# 3. Code Quality & Readability

## 3.1 Naming conventions

Use names that reveal intent.

Good names describe domain meaning, not implementation shortcuts.

Use:

- `candidateId`, `tenantId`, `approvalStatus`, `invoiceLineItems`
- `createRequisition`, `resolveTenantContext`, `calculateUsageCharge`

Avoid vague names:

- `data`
- `obj`
- `thing`
- `temp`
- `foo`
- `result2`
- `handleStuff`
- `processData`

Short names are allowed only in tiny, obvious scopes such as loop counters or simple mapping callbacks.

## 3.2 Keep functions small and focused

Each function must do one clear thing.

A function should generally:

- Have a single responsibility
- Fit comfortably on screen
- Avoid deeply nested branching
- Avoid mixing validation, persistence, authorization, external calls, and formatting in one block

If a function becomes difficult to read, split it into named helper functions with clear responsibilities.

## 3.3 Prefer self-documenting code

Code should explain itself through names, structure, and types.

Use comments only when they add value. Good comments explain why something exists, not what obvious code is doing.

Acceptable comments:

```ts
// Keep this comparison case-insensitive because provider email domains are not normalized consistently.
```

Bad comments:

```ts
// Loop through users
```

## 3.4 Keep modules cohesive

A file should contain closely related logic. Do not create dumping-ground files such as:

- `utils.ts` with unrelated functions
- `helpers.py` with mixed business logic
- `common.js` containing random shared code

Prefer domain-specific modules:

- `tenant-context.ts`
- `approval-policy.ts`
- `candidate-deduplication.py`
- `invoice-calculation.service.ts`

## 3.5 Avoid over-engineering

Do not introduce factories, abstract base classes, strategy registries, dependency injection containers, generic frameworks, or complex inheritance unless the current codebase already uses them or the need is real and immediate.

Do not build for imaginary future requirements.

A simple explicit implementation is better than a speculative abstraction.

## 3.6 Avoid under-engineering

Do not hardcode business rules that should be validated, configured, or tested. Do not ignore errors. Do not skip authorization. Do not leave TODOs in production paths.

Simple does not mean careless.

## 3.7 Keep formatting consistent

Follow the repository’s formatter and style conventions. Do not introduce a new formatting style.

Do not reformat entire files unless the task is specifically formatting-related.

## 3.8 Use strong typing where available

Use existing type systems properly.

Avoid:

- `any` unless absolutely necessary
- Unvalidated dictionaries for structured data
- Untyped API payloads
- Stringly typed domain states when enums or typed constants already exist

Prefer explicit request, response, model, and domain types.

---

# 4. Logical Rigor

## 4.1 Correctness is mandatory

The code must be logically correct, not merely syntactically valid.

Before writing code, reason through:

- Normal path
- Empty input
- Missing input
- Invalid input
- Permission denied
- Not found
- Duplicate records
- Concurrent requests
- Partial failures
- External service failure
- Retry behavior
- Timezone/date boundary behavior

## 4.2 Validate inputs at boundaries

Validate all external input at the boundary of the system:

- API request bodies
- Query parameters
- Path parameters
- Webhook payloads
- File uploads
- Environment variables
- External provider responses
- Background job payloads

Never trust client input. Never trust third-party provider input.

## 4.3 Fail safely

When code fails, it must fail in a controlled, observable, and secure way.

Do not expose internal errors, stack traces, secrets, SQL details, or provider credentials to users.

Return clear user-safe errors and log detailed internal context where appropriate.

## 4.4 Handle edge cases explicitly

Do not rely on happy-path assumptions.

For every feature, consider:

- Empty collections
- Null or missing optional values
- Duplicate submissions
- Race conditions
- Soft-deleted records
- Archived records
- Suspended users or tenants
- Revoked API keys
- Expired sessions or tokens
- Stale configuration
- Retried webhooks or jobs
- Out-of-order events

## 4.5 Preserve idempotency where required

For create, sync, webhook, payment, notification, import, and background-job operations, identify whether idempotency is required.

If required, use existing idempotency mechanisms. Do not create duplicate records when the same operation is retried.

## 4.6 Be transaction-aware

Use transactions for multi-step database changes that must succeed or fail together.

Do not perform irreversible external side effects inside a database transaction unless the architecture explicitly supports it.

Prefer outbox/event patterns for side effects that must happen after commit.

## 4.7 Be concurrency-aware

For state transitions, counters, quotas, approvals, billing, locking, and queue processing, consider concurrent updates.

Use appropriate constraints, row locks, optimistic locking, unique indexes, idempotency keys, or compare-and-swap updates.

Do not assume only one request will happen at a time.

## 4.8 State transitions must be explicit

Do not allow arbitrary status updates.

Use explicit transition rules for workflows, approvals, invoices, payments, interviews, candidates, notifications, and background jobs.

Reject invalid transitions with clear errors.

## 4.9 Dates and time must be handled carefully

Use timezone-aware date/time handling. Store timestamps consistently according to the repository’s standard, usually UTC.

Do not compare localized display strings. Do not assume server local timezone. Do not silently drop timezone information.

## 4.10 Security logic must be deny-by-default

When authorization, tenant context, role checks, or feature entitlements are unclear, deny access rather than allowing it.

Never add a permissive fallback to “make it work.”

---

# 5. Architecture & Module Boundaries

## 5.1 Follow existing boundaries

Use existing service, module, package, and schema boundaries. Do not create cross-layer shortcuts.

Examples of forbidden shortcuts:

- UI directly depending on database structures
- API handlers containing complex business logic
- Domain services importing frontend types
- One service directly mutating another service’s private tables
- Background workers bypassing authorization-sensitive domain rules

## 5.2 Separate concerns

Keep responsibilities separated:

- Controllers/routes handle transport concerns
- DTOs/schemas validate input/output shape
- Domain services enforce business rules
- Repositories/data access handle persistence
- Workers handle asynchronous execution
- Adapters handle external providers

Do not mix these layers casually.

## 5.3 Reuse existing shared utilities

Before adding new utilities, check whether the repository already has helpers for:

- Logging
- Error handling
- Pagination
- Tenant context
- Authorization
- Database sessions
- Transactions
- Idempotency
- Configuration
- Events/outbox
- Testing factories

Do not create duplicate helpers with slightly different behavior.

## 5.4 Avoid circular dependencies

Do not introduce circular imports or bidirectional module dependencies.

If two modules need to communicate, use an explicit interface, service boundary, event, or adapter.

## 5.5 Public interfaces must be stable

Be careful when changing exported functions, API responses, database contracts, event payloads, or shared types.

If a public contract must change, update all consumers and tests.

---

# 6. Data & Database Standards

## 6.1 Respect existing schema design

Do not casually alter database schema, constraints, indexes, enum values, migrations, or seed data.

Schema changes must be deliberate, reviewed, and accompanied by migrations and tests.

## 6.2 Do not bypass data integrity

Prefer database constraints where integrity matters:

- Foreign keys
- Unique constraints
- Check constraints
- Not-null constraints
- Composite keys where required
- Indexes for lookup paths

Do not enforce critical integrity only in application code.

## 6.3 No unstructured data for structured business logic

Do not introduce JSON or generic blobs for structured business data that needs querying, constraints, relationships, permissions, reporting, or lifecycle management.

Use proper relational tables, typed columns, and relationships.

JSON is acceptable only for raw immutable payloads, external provider snapshots, audit snapshots, or explicitly approved flexible metadata.

## 6.4 Migrations must be safe

Migrations must be:

- Deterministic
- Reversible where possible
- Safe for existing data
- Compatible with zero-downtime deployment where required
- Tested on a realistic database state

Do not drop columns, rename columns, rewrite large tables, or change enum values without a safe rollout plan.

## 6.5 Queries must be intentional

Avoid N+1 queries, unbounded scans, missing pagination, and unnecessary eager loading.

For list endpoints, use the repository’s pagination standard.

Do not return unlimited result sets.

## 6.6 Sensitive data must be protected

Do not log secrets, tokens, passwords, credentials, raw personally identifiable information, or private candidate data.

Use existing encryption, redaction, hashing, masking, and secrets-management utilities.

---

# 7. API Standards

## 7.1 Keep APIs consistent

Follow existing API conventions for:

- Route naming
- HTTP methods
- Status codes
- Error response shape
- Pagination
- Filtering
- Sorting
- Idempotency keys
- Versioning
- Authentication
- Authorization

Do not invent a new response format for one endpoint.

## 7.2 Validate request and response DTOs

Every API must have explicit request and response schemas or DTOs where the framework supports them.

Do not return raw database models directly from APIs.

## 7.3 Authorization must be explicit

Every protected endpoint must declare and enforce its authentication and authorization requirements.

Do not rely on frontend hiding or route naming as security.

## 7.4 Errors must be predictable

Use standard error types and messages. Include enough information for clients to correct the issue, but never leak internal details.

## 7.5 Mutations require audit consideration

For create, update, delete, state transition, permission change, billing change, credential change, and security-sensitive operations, add audit logging according to existing patterns.

---

# 8. Frontend Standards

## 8.1 Build human-usable interfaces

Frontend code must be accessible, predictable, responsive, and maintainable.

Do not build UI that only works for the happy path.

## 8.2 Use existing design system components

Use existing components, tokens, spacing, typography, forms, buttons, modals, tables, and layout primitives.

Do not create one-off styles unless necessary.

## 8.3 Handle loading, empty, error, and permission states

Every data-driven screen must handle:

- Loading state
- Empty state
- Error state
- Permission denied state
- Partial data state where applicable

## 8.4 Forms must be robust

Forms must include:

- Client-side validation where useful
- Server-side validation handling
- Clear field-level errors
- Safe submit behavior
- Disabled or loading state during submission
- Protection against accidental duplicate submit

## 8.5 Destructive actions require confirmation

Deletes, deactivations, revocations, cancellations, permission changes, billing actions, and security-sensitive actions require clear confirmation flows.

The confirmation must explain what will happen and whether the action is reversible.

## 8.6 Do not trust frontend authorization

Frontend permission checks are for user experience only. Backend authorization remains mandatory.

---

# 9. Testing Standards

## 9.1 Tests are part of the change

Any meaningful behavior change must include tests.

Do not claim a feature is complete without appropriate tests.

## 9.2 Test behavior, not implementation details

Tests should verify externally observable behavior and critical business rules.

Avoid brittle tests tied to private implementation details unless testing a low-level utility.

## 9.3 Cover edge cases

Include tests for:

- Success path
- Validation failure
- Authorization failure
- Not found
- Duplicate or idempotent request
- Invalid state transition
- Empty data
- External provider failure where relevant
- Retry behavior where relevant

## 9.4 Keep tests deterministic

Tests must not depend on real external services, current time without control, random ordering, shared mutable state, or network availability.

Use mocks, fakes, fixtures, factories, and time-freezing utilities where appropriate.

## 9.5 Do not weaken tests to pass

Never delete or weaken tests just to make a change pass unless the test is provably wrong and the reason is explained.

When changing behavior, update tests to reflect the new intended behavior.

---

# 10. Logging, Observability & Operations

## 10.1 Logs must be useful

Logs should help diagnose production issues.

Include relevant identifiers such as request ID, tenant ID, user ID, job ID, entity ID, provider, and operation name where safe and available.

Do not log sensitive data.

## 10.2 Errors must preserve context

When catching errors, either handle them meaningfully or rethrow with useful context.

Do not swallow exceptions silently.

## 10.3 Background jobs must be observable

Workers and scheduled jobs must log start, completion, failure, retry, and skipped states where appropriate.

They must be safe to retry when retry is expected.

## 10.4 Metrics matter for critical paths

For high-value operations, consider existing metric patterns for latency, success count, failure count, retry count, and queue depth.

Do not invent a separate metrics system.

---

# 11. Security Standards

## 11.1 Never hardcode secrets

Do not hardcode passwords, API keys, tokens, private keys, connection strings, encryption keys, or credentials.

Use environment variables, secret stores, or existing configuration mechanisms.

## 11.2 Do not expose sensitive data

Do not expose sensitive data in:

- API responses
- Logs
- Errors
- Frontend state
- URLs
- Analytics events
- Test snapshots

## 11.3 Authentication and authorization are mandatory

Do not add unauthenticated access to protected resources.

Do not bypass permission checks for convenience.

Do not add temporary admin bypasses.

## 11.4 External inputs require verification

Verify signatures, tokens, origins, or credentials for external webhooks, callbacks, and provider requests.

Reject unverifiable requests.

## 11.5 Use secure defaults

Default to:

- Deny access
- Private visibility
- No external sharing
- Minimal scopes
- Least privilege
- Secure cookie/session settings
- Explicit opt-in for risky behavior

---

# 12. Strict Anti-Patterns

The following are forbidden unless the user explicitly requests them and the risk is clearly documented.

## 12.1 Hallucinating dependencies

Do not import packages that are not already installed or declared in the project.

Before using a dependency, check existing package files and lock files.

Do not invent library APIs. Verify usage against existing code or official documentation when available.

## 12.2 Hallucinating internal code

Do not assume functions, classes, models, routes, tables, columns, environment variables, or configuration keys exist.

Search the repository first.

## 12.3 Spaghetti code

Do not write tangled code with mixed responsibilities, hidden side effects, global mutable state, or unclear control flow.

Do not create giant functions or giant files.

## 12.4 Broken existing logic

Do not break existing behavior to satisfy a new request.

If a behavior must change, identify affected callers and tests.

## 12.5 Unrelated or orphaned code

Do not add unused files, unused functions, unused routes, unused components, unused migrations, unused configuration, or dead abstractions.

Every new artifact must be connected to the requested feature.

## 12.6 Fake implementations

Do not create fake production logic that silently pretends success.

Forbidden examples:

- Returning success without performing the operation
- Swallowing provider failures
- Hardcoding sample users or IDs
- Mocking real behavior in production code
- Adding placeholder authorization
- Adding TODO-only logic in critical paths

## 12.7 Overbroad catch blocks

Do not use broad exception handlers that hide errors.

Bad:

```py
try:
    do_work()
except Exception:
    pass
```

If catching a broad exception is unavoidable, log context and return or raise a controlled error.

## 12.8 Unsafe database changes

Do not drop data, remove constraints, disable RLS/security policies, weaken foreign keys, or remove indexes to make code pass.

Do not use raw SQL when the project has an established safe data-access pattern unless necessary.

## 12.9 Copy-paste programming

Do not duplicate large blocks of logic. Extract shared behavior when it is truly shared and stable.

Do not copy code from unrelated modules without adapting naming, errors, tests, and domain rules.

## 12.10 Silent security bypasses

Never add shortcuts such as:

- `isAdmin = true`
- `skipAuth = true`
- `tenantId = request.tenantId || defaultTenantId`
- `userId = userId || 'local-user'`
- `allowAll = true`

Do not use development shortcuts in production paths.

## 12.11 Hidden global state

Avoid global mutable state for request-specific, user-specific, tenant-specific, or security-sensitive data.

Use explicit context passing or established context mechanisms.

## 12.12 Unbounded operations

Do not add unpaginated list queries, unbounded exports, unlimited retries, infinite loops, or background jobs without limits.

Every loop over external or database data must have a clear bound, pagination, or streaming strategy.

---

# 13. Refactoring Rules

## 13.1 Refactor only with purpose

Refactoring is allowed when it directly supports the task, reduces risk, or improves clarity of touched code.

Do not refactor unrelated areas.

## 13.2 Preserve behavior with tests

Before refactoring complex logic, identify existing tests or add characterization tests where practical.

## 13.3 Avoid cosmetic churn

Do not rename symbols, reorder files, or reformat code unless it improves the requested change or follows project tooling.

## 13.4 Keep compatibility

When refactoring public functions or APIs, update all call sites and ensure backward compatibility where required.

---

# 14. Dependency & Package Rules

## 14.1 Prefer existing dependencies

Use dependencies already present in the project when suitable.

Do not add a new dependency for trivial functionality.

## 14.2 New dependencies require justification

A new dependency must be justified by:

- Clear need
- Active maintenance
- Security reputation
- License acceptability
- Bundle/runtime impact
- Compatibility with the project stack

## 14.3 Do not upgrade casually

Do not upgrade dependencies as part of an unrelated task.

Dependency upgrades must be isolated and tested.

---

# 15. Documentation Rules

## 15.1 Update documentation when behavior changes

If a change affects setup, APIs, configuration, environment variables, migrations, commands, or operational behavior, update the relevant documentation.

## 15.2 Keep documentation accurate

Do not document aspirational behavior as if it exists.

Do not leave stale examples.

## 15.3 Prefer practical documentation

Good documentation explains how to use, configure, test, and troubleshoot the code.

Avoid vague statements like “improves performance” without details.

---

# 16. Review Checklist Before Final Response

Before completing a task, the agent must self-review the diff against this checklist:

- The change directly addresses the user request.
- The change is scoped and does not include unrelated work.
- Existing behavior is preserved unless intentionally changed.
- Names are clear and domain-specific.
- Functions are small and readable.
- Logic handles edge cases and failures.
- Inputs are validated at boundaries.
- Authorization and security are not weakened.
- Sensitive data is not exposed.
- Database changes are safe and tested.
- Migrations are included where needed.
- Events, audit logs, or side effects are handled where required.
- Tests are added or updated for meaningful behavior changes.
- Lint/type/build/test checks have been run where possible.
- No hallucinated dependencies or APIs were introduced.
- No dead, orphaned, or unused code was added.
- The final response clearly states what changed and what was verified.

---

# 17. Required Final Response Format

At the end of a coding task, respond with the following structure:

```md
## Summary
- What was changed and why.

## Files Changed
- `path/to/file`: concise description.

## Validation
- Commands run and results.
- Commands not run, with reason.

## Notes / Risks
- Any remaining risks, assumptions, or follow-up needed.
```

Keep the final response factual. Do not exaggerate. Do not claim tests passed if they were not run.

---

# 18. Absolute Rules

The agent must never:

1. Write code without first understanding the existing implementation.
2. Invent dependencies, APIs, tables, files, or environment variables.
3. Bypass authentication, authorization, tenant isolation, validation, or audit requirements.
4. Add unrelated code or broad rewrites.
5. Hide errors with silent catches.
6. Return fake success from production code.
7. Log secrets or sensitive data.
8. Remove tests or weaken checks to make code pass.
9. Introduce unbounded queries, retries, loops, or exports.
10. Claim completion without validation.

If the requested task conflicts with these rules, stop and explain the conflict before making changes.
