---
name: frontend-testing
description: Write or review frontend unit and component integration tests with Testing Library and the project test runner. Use for user-visible behavior, async states, accessibility assertions, and network boundaries; browser end-to-end workflows belong to Playwright tooling.
---

# Frontend unit and component testing

Inspect the installed runner, DOM environment, setup, and existing tests. Reuse them;
do not require Vitest or replace Jest to apply this skill. Type checking and browser
layout/focus checks remain separate from simulated DOM tests.

For TypeScript test code, apply the installed `typescript-suite` / `typescript-syntax`
language profile; resolve it through the host skill catalog and report a missing
dependency. JavaScript tests do not require TypeScript conventions.

Read [Behavioral tests](references/behavioral-tests.md) for test selection, async
interactions, and isolation. [Sources](references/sources.md) records local provenance.
Test the requested behavior at the smallest layer that can detect the real regression.
Do not add tests that simply restate implementation details or scaffold file content.

When actual browser end-to-end coverage is requested and `playwright-tools` is
available, use its testing/configuration skills. It is an optional companion, not a
required dependency; do not duplicate its workflows here or claim component tests
establish browser behavior.

## Review Checklist

- [ ] Tests exercise observable behavior or meaningful pure business rules.
- [ ] Queries and interactions reflect accessible user actions where applicable.
- [ ] Async outcomes are awaited without arbitrary sleeps or retrying side effects.
- [ ] Network, timer, cache, and mock state are isolated and restored.
- [ ] Relevant failure/recovery paths are tested and browser-only limitations are explicit.
- [ ] The affected tests passed with the actual project runner, or blockers are reported.
