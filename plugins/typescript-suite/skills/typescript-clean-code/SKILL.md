---
name: typescript-clean-code
description: Design or refactor TypeScript responsibilities, SOLID contracts, dependency injection, and functional/object-oriented boundaries. Use for maintainable TypeScript in services, libraries, tools, or frontend domain logic; no React or mandatory DDD topology.
---

# TypeScript clean code and SOLID

Apply [typescript-syntax](../typescript-syntax/SKILL.md) to all authored TypeScript.
This skill owns design decisions, not a competing language style. Inspect the requested
behavior, actual change pressure, and existing architecture before creating abstractions.

Read [SOLID and boundaries](references/solid-and-boundaries.md) for the five principles,
concrete examples, and refactoring decisions. Do not add a DI container, repository per
entity, or frontend folder tree just to satisfy an acronym. Functions and classes can
both implement clear boundaries. [Sources](references/sources.md) identifies local policy.

Keep pure policy separate from I/O where there is a real seam. Consumers own narrow
ports; composition supplies implementations. For a targeted refactor, preserve behavior,
move one responsibility at a time, and validate the public contract. Record exceptions
with concrete reasons rather than declaring every abstraction a requirement.

## Review Checklist

- [ ] TypeScript language conventions come from typescript-syntax and were applied.
- [ ] Each abstraction has a current responsibility/consumer, not speculative flexibility.
- [ ] Consumer contracts are narrow and implementations preserve behavioral guarantees.
- [ ] Business policy does not depend on concrete transport/storage/framework details.
- [ ] Mutation, errors, and side effects have clear owners and meaningful tests.
- [ ] Refactoring stays within scope and validation results are reported honestly.
