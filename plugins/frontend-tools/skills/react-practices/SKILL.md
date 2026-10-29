---
name: react-practices
description: Build or review React components, Hooks, state, Effects, accessible forms, and rendering behavior. Use for React UI correctness; does not prescribe a feature folder structure or require TypeScript.
---

# React practices

Inspect the React version, framework, rendering mode, and existing state/data tools.
Keep framework conventions and server/client boundaries. Do not assume every React
project is a client-only SPA or that APIs from a newer release are available.

Use [State and Effects](references/state-and-effects.md) for state ownership,
synchronization, and performance. Use [Components and accessibility](references/components-and-accessibility.md)
for component contracts and interactions. Consult [Sources](references/sources.md)
for the local research record.

Keep render pure and component/Hook identities stable. Call ordinary Hooks at the top
level of components or custom Hooks, not conditionally or in callbacks. Follow the
installed Hooks lint rules, including API-specific exceptions rather than generalizing
those exceptions to all Hooks. Fix dependencies instead of suppressing lint warnings.

When editing TypeScript, load the installed `typescript-suite` skill `typescript-syntax`
for language conventions (including its explicit typing exceptions). It is not required
for JavaScript-only work. Resolve it through the host skill catalog; if unavailable,
report the dependency gap rather than claiming convention compliance. Use
[frontend-testing](../frontend-testing/SKILL.md) when the task requires component tests.

## Review Checklist

- [ ] Components and Hooks respect render purity, identity, and installed React rules.
- [ ] State has an explicit owner and avoids redundant or contradictory values.
- [ ] Effects synchronize external systems with dependencies and appropriate cleanup.
- [ ] Loading, empty, failure, and interaction states relevant to the task are usable.
- [ ] Changed controls have semantic markup, accessible names, and keyboard behavior.
- [ ] Relevant lint, behavior, and rendering checks passed or limitations are reported.
