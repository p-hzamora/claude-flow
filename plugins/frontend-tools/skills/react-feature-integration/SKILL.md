---
name: react-feature-integration
description: Implement a vertical feature in an existing React and TypeScript application using feature-owned UI, state, API adapters, and public exports. Use when combining React/TS behavior with feature architecture; not for standalone type fixes or project scaffolding.
---

# React and TypeScript feature integration

Inspect the requested user flow, existing architecture profile, route entry points,
and data tooling. Deliver one functioning vertical feature with the smallest public
contract. Do not install a new state/query/router library just to match an example.

This skill owns stack-specific placement and wiring. The sibling frontend skills and
the installed TypeScript dependency own their respective rules; read only those relevant to the change:

- [feature-architecture](../feature-architecture/SKILL.md): dependency direction and boundaries.
- `typescript-suite` / `typescript-syntax`: language conventions and runtime validation.
  Resolve this installed dependency through the host skill catalog; report a missing
  dependency instead of claiming TypeScript convention compliance.
- [react-practices](../react-practices/SKILL.md): component, state, and Effect behavior.
- [frontend-testing](../frontend-testing/SKILL.md): behavioral tests when needed.

Read [Vertical feature recipe](references/vertical-feature.md) for file ownership and
integration decisions. [Sources](references/sources.md) explains the local synthesis.
Apply the project's established rules without loading every reference for a small edit.

## Review Checklist

- [ ] Route/app composition consumes the feature's deliberate public contract.
- [ ] UI, model, and transport responsibilities have appropriate owners.
- [ ] Remote data, drafts, and URL state each have a defined source of truth.
- [ ] The requested flow handles relevant pending, empty, success, and failure states.
- [ ] Boundary validation, user-facing behavior, and imports were checked at the changed seams.
