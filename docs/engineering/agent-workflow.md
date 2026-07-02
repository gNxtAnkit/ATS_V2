# Agent and Coding Workflow

Before changing code:

1. Read `AGENTS.md`.
2. Inspect existing files and patterns.
3. Read the relevant phase and architecture docs.
4. Produce a short implementation plan for non-trivial work.
5. Keep changes scoped to the request.

After changing code:

1. Run the smallest relevant validation command.
2. Fix issues caused by the change.
3. Report what changed, what was checked, what was not checked, and remaining risk.

Agents must not implement business features before their phase, invent dependencies, bypass service boundaries, add fake production flows, or weaken tests.
