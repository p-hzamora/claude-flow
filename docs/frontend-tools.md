# frontend-tools

Independent frontend skills for React and TypeScript applications organized by feature.
All guidance and references ship locally; no external URLs, remote includes, or automatic
research downloads are embedded in the plugin.

**Version:** 0.2.0
**Dependencies:** `typescript-suite` (Claude Code dependency; install explicitly in Codex)

The Claude Code and Codex manifests point to the same skill files. This plugin adds no
agents or host-specific copies; TypeScript roles belong to typescript-suite. Every skill
ends with a task-specific Review Checklist.

## Skills

| Skill | Responsibility | Local references |
|---|---|---|
| [typescript-practices](../plugins/frontend-tools/skills/typescript-practices/SKILL.md) | Compatibility entry point forwarding to typescript-suite; owns no language rules. | Migration record. |
| [react-practices](../plugins/frontend-tools/skills/react-practices/SKILL.md) | Components, Hooks, state, Effects, accessible interactions, and rendering. Works with JavaScript too. | State and Effects; components and accessibility; sources. |
| [feature-architecture](../plugins/frontend-tools/skills/feature-architecture/SKILL.md) | Framework-independent ownership, dependency direction, public exports, and incremental migration. | Boundaries and layouts; migration and enforcement; sources. |
| [react-feature-integration](../plugins/frontend-tools/skills/react-feature-integration/SKILL.md) | Wire one React/TS vertical feature into an existing app; compose the narrower skills as needed. | Vertical feature recipe; sources. |
| [frontend-scaffolding](../plugins/frontend-tools/skills/frontend-scaffolding/SKILL.md) | Initialize an app or feature safely, preserve tooling, and verify a small working result. | Scaffolding workflow; sources. |
| [frontend-testing](../plugins/frontend-tools/skills/frontend-testing/SKILL.md) | Unit and component integration tests using the existing runner and Testing Library. | Behavioral tests; sources. |

## Selection and composition

Use `typescript-suite` / `typescript-syntax` for type/API-boundary fixes, React alone
for JavaScript Hook/component issues, and feature architecture alone for ownership
or dependency design. TypeScript changes use the canonical language profile. The integration
skill connects those concerns when implementing a complete feature. Scaffolding owns
initialization mechanics rather than duplicating the architecture rules. Testing is
independent of the chosen folder layout and does not require a particular test runner.

The default architecture is a lightweight app/pages/features/shared profile. Formal
Feature-Sliced Design is an explicit alternative for projects that want its layers and
rules. Neither requires empty folders or a state/query/router library. Existing framework
routing and server/client boundaries take precedence over illustrative folder trees.

`playwright-tools` is an optional companion for browser end-to-end work. An explicitly
selected template catalog can use the existing `scaffold-catalog` skill for rendering;
ordinary frontend scaffolding has no catalog dependency.

## Research and maintenance

Primary documentation reviewed on 2026-10-22: Microsoft TypeScript and TSConfig,
React, Feature-Sliced Design, Vite, typescript-eslint, Testing Library, and W3C WAI.
The TypeScript compatibility entry records its migration; other skills'
`references/sources.md` record relevant titles and distinguish upstream
rules from local design recommendations. References are original summaries, not copied
manuals. External links are deliberately omitted so skill execution has no dependency
on mutable remote guidance. This does not remove normal package supply-chain risks;
scaffolding still checks versions and respects installation permissions.

Future research is a deliberate maintenance change followed by validation and a version
release. Ordinary skill invocation reads local guidance and installed project metadata.

## Install

Claude Code:

```text
/plugin install frontend-tools
```

Codex, after adding this marketplace:

```text
codex plugin add typescript-suite@claude-flow
codex plugin add frontend-tools@claude-flow
```

Example requests:

- “Review this TypeScript code for unsafe assertions and unnecessary abstractions.”
- “Fix this React Effect and preserve keyboard behavior.”
- “Design feature boundaries for checkout and account settings.”
- “Implement edit-profile in this React/TS feature-based app.”
- “Scaffold a small React/TS SPA using the lightweight feature profile.”
- “Test this form's failed submission and retry behavior.”
