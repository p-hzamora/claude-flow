---
name: typescript-testing
description: Write or review framework-independent TypeScript unit, contract, and type tests with the existing runner. Use for business rules, adapters, asynchronous behavior, and compile-time API guarantees; React DOM and browser tests stay in frontend tooling.
---

# TypeScript testing

Read [typescript-syntax](../typescript-syntax/SKILL.md) before authoring test code;
tests do not justify unsafe casts or partial objects disguised as full contracts.
Inspect the existing runner, compilation/type-check commands, environment, and fixtures.
Use [Behavior and type contracts](references/behavior-and-type-contracts.md) for test
selection, doubles, async checks, and negative type cases. [Sources](references/sources.md)
records the basis of this skill.

Use the existing runner. Do not migrate Jest to Vitest or add DOM libraries to test
pure TypeScript. Frontend component testing and Playwright remain separate optional
workflows. Run runtime tests and the applicable type check separately when the runner
only transforms TypeScript. Report which guarantees each check covers.

## Review Checklist

- [ ] Tests exercise observable contracts, business invariants, or meaningful type guarantees.
- [ ] Test code follows typescript-syntax; doubles implement the actual required capability.
- [ ] Async outcomes and rejection paths are awaited; time and shared state are isolated.
- [ ] Negative type tests are compiled and narrow enough to demonstrate the intended failure.
- [ ] Runtime tests and type checks ran where applicable; coverage gaps are described without invented thresholds.
