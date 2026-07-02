# Engineering Standards

The mandatory rules in `AGENTS.md` govern all code changes.

## Code Quality

- Keep code simple, typed, readable, and modular.
- Prefer explicit names and straightforward control flow.
- Avoid clever abstractions and speculative frameworks.
- Avoid unused dependencies and unrelated helpers.
- Avoid circular imports.
- Do not add fake business logic.

## Security

- Default to deny.
- Do not bypass authentication, authorization, tenant isolation, validation, RLS, or audit requirements.
- Do not log secrets, tokens, candidate PII, billing data, or private security events.
- Sensitive data access must be minimized and audited.

## TODO Format

Use clear phase-scoped TODOs:

```text
TODO(Phase 2 - Identity Service): Replace this placeholder with real auth middleware.
```
